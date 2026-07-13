"""Deep property + owner research via Claude web search.

Realtor.com only carries ON-market listings, so owned homes (the typical
walkthrough client) come back empty. This module researches the property from
public web sources (county assessor / tax records, GIS, FEMA, zoning code,
Zillow/Redfin public pages) using Claude's server-side web_search + web_fetch
tools, and returns:

  - property_details : same dict shape document_generator consumes, filled from
                       public records instead of Realtor
  - feasibility      : renovation-relevant site notes (zoning envelope, flood,
                       sewer/septic signal, sale history)
  - owner_summary    : ownership confirmation + PUBLIC professional context only
                       (never personal/financial/social digging)
  - sources          : cited URLs

It never raises to the caller — returns None on any failure so the report
pipeline degrades gracefully.
"""
import json
import logging
import time
from typing import Any, Dict, Optional

try:
    import anthropic
except ImportError:  # keep import-safe for environments without the SDK
    anthropic = None

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-4-8"

# Structured-output schema (strings throughout so "Information not available"
# is always valid and the report's suppression logic can handle blanks).
_RESEARCH_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "found", "address_resolves", "property_kind",
        "bedrooms", "bathrooms", "sqft", "year_built", "property_type",
        "lot_size", "last_sale_price", "last_sale_date", "assessed_value",
        "property_taxes", "zoning", "flood_zone", "neighborhood", "feasibility_notes",
        "owner_summary", "photo_url", "floor_plan_url", "listing_url", "sources",
    ],
    "properties": {
        "found": {"type": "boolean", "description": "true only if THIS specific property was identified in public records"},
        "address_resolves": {"type": "boolean", "description": "true if the address is a specific real parcel/building/unit with property records; false for a park, landmark, general area, or an address with no street number"},
        "property_kind": {"type": "string", "enum": ["residential", "non_residential", "not_a_parcel", "unknown"], "description": "one of exactly: residential, non_residential, not_a_parcel, unknown"},
        "bedrooms": {"type": "string"},
        "bathrooms": {"type": "string"},
        "sqft": {"type": "string", "description": "living area square footage"},
        "year_built": {"type": "string"},
        "property_type": {"type": "string", "description": "e.g. Single Family, Condo, Multi-Family"},
        "lot_size": {"type": "string", "description": "acreage or dimensions"},
        "last_sale_price": {"type": "string"},
        "last_sale_date": {"type": "string"},
        "assessed_value": {"type": "string"},
        "property_taxes": {"type": "string", "description": "annual property taxes"},
        "zoning": {"type": "string", "description": "zoning district + key setback/lot-coverage limits if found"},
        "flood_zone": {"type": "string", "description": "FEMA flood zone designation"},
        "neighborhood": {"type": "string"},
        "feasibility_notes": {
            "type": "array", "items": {"type": "string"},
            "description": "renovation-relevant facts: sewer vs septic signal, additions/permits on record, lot-coverage headroom, flood implications, etc.",
        },
        "owner_summary": {
            "type": "string",
            "description": "Short labeled lines separated by newlines (Ownership / Tenure / Profession / Business-Employer / Other properties / For the meeting). PUBLIC professional and property-record context only — no personal, financial, family, or social-media details.",
        },
        "photo_url": {"type": "string", "description": "a DIRECT image URL (ending .jpg/.jpeg/.png/.webp) of the property's main exterior/listing photo if publicly available, else 'Information not available'"},
        "floor_plan_url": {"type": "string", "description": "a DIRECT image URL (ending .jpg/.jpeg/.png/.webp/.gif) of a FLOOR PLAN for this specific home/unit if publicly available (current or past StreetEasy/Zillow/Realtor listing, or a condo/co-op line/stack plan), else 'Information not available'"},
        "listing_url": {"type": "string", "description": "the URL of the property's most relevant current or past public listing page (StreetEasy/Zillow/Realtor), a good place to find the floor plan and photos, else 'Information not available'"},
        "sources": {"type": "array", "items": {"type": "string", "description": "source URL"}},
    },
}


def _research_prompt(address: str, owner_name: Optional[str],
                     owner_email: Optional[str] = None, owner_phone: Optional[str] = None) -> str:
    person = owner_name.strip() if owner_name else None
    # Client-provided contact details (from the consultation) — used ONLY to
    # confirm WHICH public professional profile is the right person when the name
    # is common. Not for personal-life profiling.
    contacts = []
    if owner_email and str(owner_email).strip():
        contacts.append(f"email {str(owner_email).strip()}")
    if owner_phone and str(owner_phone).strip():
        contacts.append(f"phone {str(owner_phone).strip()}")
    contact_line = (
        "  - DISAMBIGUATE a common name: pull the ACRIS/county DEED for the exact legal owner name "
        "(with middle initial or LLC/trust if any). The client gave these contact details on the call — "
        "use them to CONFIRM which specific public professional profile is this person (e.g. the same "
        f"{' or '.join(contacts)} appearing on a company page, professional bio, or profile): "
        f"{', '.join(contacts)}. Use them ONLY to pin the correct professional identity — never to "
        "compile personal-life information. If it still can't be uniquely confirmed, list the candidate "
        "profiles and say 'verify in person'.\n"
        if contacts else
        "  - DISAMBIGUATE a common name using the ACRIS/county DEED for the exact legal owner name; if "
        "still ambiguous, list the candidate profiles and say 'verify in person'.\n"
    )
    person_line = (
        f"The salesperson's walkthrough is with: {person}. Treat this person as the primary subject. "
        f"First confirm whether {person} is the current owner of record from the public deed/tax record; "
        f"if the record shows a different owner, report BOTH and flag the mismatch.\n"
        if person else
        "Identify the current owner of record from the public deed/tax record.\n"
    ) + contact_line
    return (
        "You are preparing an internal pre-walkthrough research brief for a renovation contractor's "
        "salesperson, who will meet the client at the property. Be THOROUGH and specific — this brief "
        "should let the rep walk in fully informed. Research:\n\n"
        f"    {address}\n\n"
        "=== FIRST: CLASSIFY THE ADDRESS ===\n"
        "Decide what this address actually is and set two fields accordingly:\n"
        "  - a specific home / condo / co-op unit -> address_resolves=true, property_kind='residential'\n"
        "  - a specific commercial / mixed-use / institutional building -> address_resolves=true, property_kind='non_residential'\n"
        "  - a PARK, landmark, open space, general area, or an address with NO street number (nothing to "
        "look up as an individual parcel) -> address_resolves=false, property_kind='not_a_parcel'\n"
        "  - genuinely unsure -> property_kind='unknown'\n"
        "If not_a_parcel, do NOT invent parcel facts (beds/baths/sqft/owner): set those to 'Information "
        "not available' and instead give useful AREA context in feasibility_notes (typical building "
        "stock, zoning, historic-district risk, permit path).\n\n"
        "=== OBJECTIVE 1: THE PERSON (owner / first-call contact) ===\n"
        + person_line +
        "Then gather PUBLIC, professionally-relevant context to help the rep gauge project scope/budget "
        "and build rapport:\n"
        "  - how long they have owned this home, and the purchase price/date (public record)\n"
        "  - their profession, job title, and the employer or business they own or run\n"
        "  - public professional profiles (LinkedIn, company website, professional bios, licensing "
        "boards, notable press) — VERIFY it is the same person (matching locale/role); if a profile "
        "might be a different individual with the same name, say so explicitly and do NOT rely on it\n"
        "  - any OTHER properties they own per public records (a portfolio/repeat-client signal)\n"
        "Compose owner_summary as short labeled lines separated by newlines, for example:\n"
        "  'Ownership: ...' / 'Tenure: ...' / 'Profession: ...' / 'Business/Employer: ...' / "
        "'Other properties: ...' / 'For the meeting: ...'.\n"
        "For the Profession / Business-Employer lines specifically: if you can uniquely confirm the "
        "person, state it plainly. If you CANNOT uniquely confirm (common name), do NOT leave it just "
        "'Information not available' — instead give the most likely public professional candidate(s) for "
        "this name in this area as clearly-labeled UNCONFIRMED leads (e.g. 'Likely finance — a Kapil "
        "Gupta is a Managing Director at UBS; a physician and a tech founder also share the name — "
        "unconfirmed, verify in person'). Use 'Information not available' only if you truly found NO "
        "public professional profile for the name at all. Never assert a single identity you have not "
        "verified.\n"
        "PRIVACY BOUNDARY (strict): PUBLIC professional and property-record information ONLY. Do NOT "
        "compile personal finances/income/net-worth estimates, family or household details, or "
        "social-media / personal-life profiling. If something is not publicly and professionally "
        "relevant, leave it out.\n\n"
        "=== OBJECTIVE 2: THE PROPERTY (building, unit, and site) ===\n"
        "Get everything available:\n"
        "  - beds, baths, interior living square footage, year built, number of stories/floors, "
        "property type, lot size. NOTE: bedroom/bathroom counts are usually NOT in assessor/tax records "
        "— they are on LISTING pages (Zillow, Trulia, Realtor.com, Redfin, StreetEasy), shown as e.g. "
        "'4 bd | 3 ba'. Open a current or past listing for this exact address to get the bed/bath count; "
        "do not report beds/baths as unavailable without checking a listing.\n"
        "  - for a CONDO or CO-OP unit: the UNIT's beds/baths/interior sqft and floor from listing "
        "history, PLUS building info (year built, number of units/stories), the monthly HOA / "
        "maintenance / common charges, and whether it is a condo vs. co-op\n"
        "  - last sale price & date, and prior sale history if available. If the last recorded sale is "
        "clearly NON-ARM'S-LENGTH or far below market (e.g. $1, a nominal/intra-family transfer, or a "
        "price far under the unit's own recent listing/comparable sales), do NOT present it as the plain "
        "value — append a short flag in last_sale_price like '(below-market/non-arm's-length transfer; "
        "listed ~$770K)' so the rep isn't misled about value\n"
        "  - assessed value and annual property taxes\n"
        "  - zoning district with setback / lot-coverage / FAR limits\n"
        "  - FEMA flood zone\n"
        "  - renovation-relevant feasibility: municipal sewer vs. septic, any additions / permits / DOB "
        "records, landmark or historic-district status, and whether the lot/unit has room to build out "
        "or reconfigure within the zoning/board envelope\n"
        "  - if a public listing shows a main exterior photo, capture its DIRECT image URL (ending "
        ".jpg/.jpeg/.png/.webp) as photo_url; leave it 'Information not available' if none is clearly a "
        "direct image link\n"
        "  - FLOOR PLAN (high priority): actively hunt for one. A floor plan is a TOP-DOWN SCHEMATIC "
        "LINE DRAWING of the unit layout (rooms, walls, dimensions) — it is NOT a photograph of a room. "
        "Check the property's CURRENT and PAST listings on StreetEasy, Zillow, Realtor.com, and "
        "CityRealty, and for a condo/co-op the building's line/stack floor plans. Once you find the "
        "listing page, FETCH IT and look specifically for the floor-plan diagram image (often labeled "
        "'floor plan' and visually a schematic, not a photo). Return that direct image URL as "
        "floor_plan_url. Do NOT return a room/interior/exterior PHOTO as floor_plan_url — if you cannot "
        "find an actual floor-plan diagram, set floor_plan_url to 'Information not available' (a photo "
        "does not count). ALWAYS return the best listing page URL as listing_url (where the rep can open "
        "the floor plan and photos).\n\n"
        "=== SOURCES ===\n"
        "Use authoritative PUBLIC sources and cross-check. For NYC: StreetEasy, PropertyShark, ACRIS "
        "(a836-acris.nyc.gov), NYC ZoLa (zola.planning.nyc.gov), DOB NOW / BIS, and NYC landmark maps. "
        "For NJ: njpropertyrecords, njparcels, and the county tax assessor. For CT/other: the county or "
        "town assessor (e.g. vgsi) and GIS. Everywhere: Zillow/Redfin/Realtor/Trulia listing history, and "
        "FEMA msc.fema.gov for flood. Prefer the county/assessor record for lot/sqft/year/taxes/sale, and "
        "LISTING pages for beds/baths and floor plans (assessor records usually omit bed/bath counts).\n\n"
        "\n=== GOAL ===\n"
        "The salesperson should NOT have to research anything again before the walkthrough. Be "
        "exhaustive on building/unit details, and do your best to capture the floor plan, a photo, and "
        "the listing URL if they exist publicly.\n\n"
        "Be factual and cite your sources. If a specific fact cannot be found, use the exact phrase "
        "'Information not available' for it rather than guessing."
    )


# Property-fact fields the gap-fill pass may backfill (owner/classification excluded).
_PROPERTY_FACT_KEYS = (
    "bedrooms", "bathrooms", "sqft", "year_built", "property_type", "lot_size",
    "last_sale_price", "last_sale_date", "assessed_value", "property_taxes",
    "zoning", "flood_zone", "neighborhood",
)
# Core facts worth a second targeted pass when the first leaves them blank.
_CORE_FIELDS = ("bedrooms", "bathrooms", "sqft", "year_built")
# Skip the (optional) gap-fill pass if pass 1 already consumed this much wall
# clock, so pass1 + gap-fill stays well under the 600s gunicorn worker window
# even on a slow-tail run.
_GAPFILL_SKIP_AFTER = 240.0


def _field(data: Optional[Dict[str, Any]], key: str) -> str:
    """Read a research field, mapping missing/empty to the sentinel string."""
    val = str((data or {}).get(key) or "").strip()
    return val if val else "Information not available"


def _gap_prompt(address: str, missing: list) -> str:
    """Focused follow-up prompt for only the still-missing core property facts."""
    labels = {
        "bedrooms": "number of bedrooms", "bathrooms": "number of bathrooms",
        "sqft": "interior living square footage", "year_built": "year built",
    }
    want = ", ".join(labels.get(m, m) for m in missing)
    need_beds = any(m in ("bedrooms", "bathrooms") for m in missing)
    beds_hint = (
        "CRITICAL — bedrooms & bathrooms: assessor/tax records usually OMIT these; they live on LISTING "
        "sites, which are JS-heavy so FETCHING the page often returns nothing useful. Instead run "
        "SEPARATE web searches — '<address> Zillow', '<address> Trulia', '<address> Redfin', "
        "'<address> Realtor', '<address> bedrooms bathrooms' — because the SEARCH-RESULT SNIPPETS "
        "themselves display the count (e.g. '4 bd, 3.5 ba, 3,768 sqft'), even for SOLD or off-market "
        "homes (these sites retain the full sold record). Read the count straight from the snippets. "
        "ALSO check the county PROPERTY APPRAISER / assessor record — many jurisdictions list "
        "'Bedrooms' and 'Bathrooms' fields directly (e.g. Miami-Dade PA at miamidadepa.gov, and most "
        "FL/CA/TX/GA counties) and their record pages are far less JS-heavy than Zillow, so FETCH the "
        "appraiser record page and read the counts there too. Bathrooms are the most-often-missed — "
        "cross-check listing snippets AND the appraiser card specifically for the bath count. Report the "
        "NUMERIC counts (e.g. bedrooms '4', bathrooms '3.5').\n"
        if need_beds else ""
    )
    return (
        f"Focused follow-up for the SPECIFIC property at:\n\n    {address}\n\n"
        f"Find ONLY these still-missing facts: {want}.\n"
        + beds_hint +
        "For square footage / year built, use BOTH a listing and the county/city assessor or tax "
        "record (for NYC search the BBL on PropertyShark / ACRIS / NYC DOF). Fetch a page if needed. "
        "Report each fact with its source. Use 'Information not available' only if it genuinely cannot "
        "be found — do not guess."
    )


def research_property(
    address: str,
    anthropic_api_key: str,
    owner_name: Optional[str] = None,
    owner_email: Optional[str] = None,
    owner_phone: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    effort: str = "low",
    max_searches: int = 8,
    max_fetches: int = 3,   # fetches enable floor-plan/listing retrieval; the ~2-min
                            # report time is fine because delivery is async (POST 0.1s
                            # + poll — no 120s synchronous limit)

    use_thinking: bool = False,
    timeout: float = 420.0,
) -> Optional[Dict[str, Any]]:
    """Research a property (and lightly, its owner) from public web sources.

    Tuned for DEPTH within a bounded latency budget: basic web search (no
    dynamic-filtering code-exec), a couple of targeted page fetches, no extended
    thinking, and a strict per-call client timeout so one report can never hang.
    The hard timeout + max_retries=0 guarantee a graceful None on a slow run
    rather than a stuck worker. (Extended thinking + the dynamic-filtering tools
    are what previously pushed this to 15+ minutes; they stay off.)

    First classifies the address (residential / non_residential / not_a_parcel)
    so the report can adapt — a park or place-name yields no parcel facts by
    design, not by failure. For a resolvable residential parcel still missing
    core facts (beds/baths/sqft/year) after the first pass, runs one bounded
    gap-fill pass and merges only the blanks.

    Returns {found, address_resolves, property_kind, property_details,
    feasibility, owner_summary, sources, zoning, flood_zone} or None on any
    failure/timeout. Never raises.
    """
    if anthropic is None or not anthropic_api_key or not address:
        logger.info("Property research skipped (no SDK / key / address)")
        return None
    try:
        # Hard client-side timeout + no retries so one report can't hang for
        # tens of minutes on a slow search loop.
        client = anthropic.Anthropic(api_key=anthropic_api_key, timeout=timeout, max_retries=0)
        _start = time.monotonic()

        def _run_search(prompt: str, n_search: int, n_fetch: int) -> str:
            """One research round: basic web search (+ optional fetch), following
            pause_turn continuations. Basic tools (not the _20260209 dynamic-
            filtering variant) keep it fast."""
            tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": n_search}]
            if n_fetch > 0:
                tools.append({"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": n_fetch})
            kwargs = dict(model=model, max_tokens=6000, output_config={"effort": effort}, tools=tools)
            if use_thinking:
                kwargs["thinking"] = {"type": "adaptive"}
            msgs = [{"role": "user", "content": prompt}]
            resp = None
            for _ in range(4):  # allow a few pause_turn continuations
                resp = client.messages.create(messages=msgs, **kwargs)
                if resp.stop_reason == "pause_turn":
                    msgs.append({"role": "assistant", "content": resp.content})
                    continue
                break
            return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")

        def _structure(research_text: str) -> Optional[Dict[str, Any]]:
            """Structure research prose into the schema; salvage wrapped JSON."""
            struct = client.messages.create(
                model=model, max_tokens=6000,  # headroom so the JSON isn't truncated
                messages=[{"role": "user", "content": (
                    "Extract the property research below into the required JSON. Use the exact string "
                    "'Information not available' for any field the research did not establish. Do not "
                    "invent values.\n\n--- RESEARCH ---\n" + research_text)}],
                output_config={"effort": "low", "format": {"type": "json_schema", "schema": _RESEARCH_SCHEMA}},
            )
            raw = next((b.text for b in struct.content if getattr(b, "type", None) == "text"), "")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                import re as _re
                m = _re.search(r"\{.*\}", raw, _re.DOTALL)
                return json.loads(m.group(0)) if m else None

        def _looks_like_floor_plan(url: str) -> bool:
            """Vision-verify a candidate floor_plan_url is an actual schematic, not
            a room photo the model mislabeled. Conservative: any error/uncertainty
            counts as NOT a floor plan (better a link than a wrong image)."""
            try:
                v = client.messages.create(
                    model="claude-haiku-4-5", max_tokens=10,
                    messages=[{"role": "user", "content": [
                        {"type": "image", "source": {"type": "url", "url": url}},
                        {"type": "text", "text": "Is this image an architectural FLOOR PLAN (a top-down "
                         "schematic diagram of a room layout with walls/room labels), or a PHOTO / "
                         "something else? Answer with exactly one word: FLOORPLAN or OTHER."}]}],
                )
                ans = "".join(b.text for b in v.content if getattr(b, "type", None) == "text").strip().upper()
                return ans.startswith("FLOORPLAN")
            except Exception as e:
                logger.info("Floor-plan vision check failed for %s (%s) — treating as not a floor plan",
                            url, type(e).__name__)
                return False

        # Pass 1: full research + structuring.
        research_text = _run_search(_research_prompt(address, owner_name, owner_email, owner_phone),
                                    max_searches, max_fetches)
        if not research_text.strip():
            logger.info("Property research produced no text for '%s'", address)
            return None
        data = _structure(research_text)
        if not data:
            logger.warning("Property research structuring returned unparseable JSON for '%s'", address)
            return None

        address_resolves = bool(data.get("address_resolves", True))
        # Canonicalize spaces AND hyphens ("non-residential" -> "non_residential")
        # so a natural-orthography value still matches the renderer's checks.
        property_kind = str(data.get("property_kind") or "unknown").strip().lower().replace(" ", "_").replace("-", "_")

        # Pass 2 (gap-fill): only for a resolvable RESIDENTIAL parcel still missing
        # core facts. Bounded (fewer searches, one fetch) so latency stays in
        # budget; merges only blanks — never overwrites a pass-1 value.
        if address_resolves and property_kind in ("residential", "unknown"):
            missing = [f for f in _CORE_FIELDS if _field(data, f) == "Information not available"]
            elapsed = time.monotonic() - _start
            if missing and elapsed > _GAPFILL_SKIP_AFTER:
                logger.info("Skipping gap-fill for '%s' — pass 1 took %.0fs (>%.0fs), staying under the worker window",
                            address, elapsed, _GAPFILL_SKIP_AFTER)
                missing = []
            if missing:
                logger.info("Gap-fill pass for '%s' (missing: %s)", address, ", ".join(missing))
                try:
                    gap_text = _run_search(_gap_prompt(address, missing), 5, 2)  # room to fetch a listing page
                    gap = _structure(gap_text) if gap_text.strip() else None
                    if gap:
                        for k in _PROPERTY_FACT_KEYS:
                            if _field(data, k) == "Information not available" and _field(gap, k) != "Information not available":
                                data[k] = gap[k]
                        merged, seen = [], set()
                        for s in list(data.get("sources") or []) + list(gap.get("sources") or []):
                            s = str(s).strip()
                            if s and s not in seen:
                                seen.add(s); merged.append(s)
                        data["sources"] = merged
                except Exception as e:
                    logger.info("Gap-fill pass failed for '%s' (keeping pass-1 data): %s", address, e)

        # Reject a mislabeled photo passed off as a floor plan (vision check).
        fp = _field(data, "floor_plan_url")
        if fp != "Information not available" and str(fp).startswith(("http://", "https://")):
            if not _looks_like_floor_plan(str(fp)):
                logger.info("Rejected non-floor-plan image as floor_plan_url for '%s': %s", address, fp)
                data["floor_plan_url"] = "Information not available"

        property_details = {
            "address": address,
            # This pipeline researches OWNED (off-market) homes — there is no
            # active list price, so leave 'price' as the sentinel. The document
            # generator then renders the sale under a "Last Sold Price" label
            # instead of mislabeling a years-old purchase as the current price.
            "price": "Information not available",
            "last_sold_price": _field(data, "last_sale_price"),
            "last_sold_date": _field(data, "last_sale_date"),
            "bedrooms": _field(data, "bedrooms"),
            "bathrooms": _field(data, "bathrooms"),
            "sqft": _field(data, "sqft"),
            "year_built": _field(data, "year_built"),
            "property_type": _field(data, "property_type"),
            "lot_size": _field(data, "lot_size"),
            "assessed_value": _field(data, "assessed_value"),
            "property_taxes": _field(data, "property_taxes"),
            "neighborhood": _field(data, "neighborhood"),
            "photo_url": _field(data, "photo_url"),
            "floor_plan_url": _field(data, "floor_plan_url"),
            "listing_url": _field(data, "listing_url"),
            "photos": [],
            "floor_plans": [],
            "source": "public records research",
        }
        return {
            "found": bool(data.get("found")),
            "address_resolves": address_resolves,
            "property_kind": property_kind,
            "property_details": property_details,
            "zoning": _field(data, "zoning"),
            "flood_zone": _field(data, "flood_zone"),
            "feasibility": [s for s in (data.get("feasibility_notes") or []) if str(s).strip()],
            "owner_summary": _field(data, "owner_summary"),
            "sources": [s for s in (data.get("sources") or []) if str(s).strip()],
        }
    except Exception as e:  # never break the pipeline
        logger.warning("Property research failed for '%s': %s", address, e)
        return None
