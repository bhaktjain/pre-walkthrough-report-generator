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
        "owner_summary", "sources",
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
        "sources": {"type": "array", "items": {"type": "string", "description": "source URL"}},
    },
}


def _research_prompt(address: str, owner_name: Optional[str]) -> str:
    person = owner_name.strip() if owner_name else None
    person_line = (
        f"The salesperson's walkthrough is with: {person}. Treat this person as the primary subject. "
        f"First confirm whether {person} is the current owner of record from the public deed/tax record; "
        f"if the record shows a different owner, report BOTH and flag the mismatch.\n"
        if person else
        "Identify the current owner of record from the public deed/tax record.\n"
    )
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
        "'Other properties: ...' / 'For the meeting: ...'. Include only lines you have real public info for.\n"
        "PRIVACY BOUNDARY (strict): PUBLIC professional and property-record information ONLY. Do NOT "
        "compile personal finances/income/net-worth estimates, family or household details, or "
        "social-media / personal-life profiling. If something is not publicly and professionally "
        "relevant, leave it out.\n\n"
        "=== OBJECTIVE 2: THE PROPERTY (building, unit, and site) ===\n"
        "Get everything available:\n"
        "  - beds, baths, interior living square footage, year built, number of stories/floors, "
        "property type, lot size\n"
        "  - for a CONDO or CO-OP unit: the UNIT's beds/baths/interior sqft and floor from listing "
        "history, PLUS building info (year built, number of units/stories), the monthly HOA / "
        "maintenance / common charges, and whether it is a condo vs. co-op\n"
        "  - last sale price & date, and prior sale history if available\n"
        "  - assessed value and annual property taxes\n"
        "  - zoning district with setback / lot-coverage / FAR limits\n"
        "  - FEMA flood zone\n"
        "  - renovation-relevant feasibility: municipal sewer vs. septic, any additions / permits / DOB "
        "records, landmark or historic-district status, and whether the lot/unit has room to build out "
        "or reconfigure within the zoning/board envelope\n\n"
        "=== SOURCES ===\n"
        "Use authoritative PUBLIC sources and cross-check. For NYC: StreetEasy, PropertyShark, ACRIS "
        "(a836-acris.nyc.gov), NYC ZoLa (zola.planning.nyc.gov), DOB NOW / BIS, and NYC landmark maps. "
        "For NJ: njpropertyrecords, njparcels, and the county tax assessor. For CT/other: the county or "
        "town assessor (e.g. vgsi) and GIS. Everywhere: Zillow/Redfin/Realtor listing history, and FEMA "
        "msc.fema.gov for flood. Prefer the county/assessor record for facts.\n\n"
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
    return (
        f"Focused follow-up for the SPECIFIC property at:\n\n    {address}\n\n"
        f"Find ONLY these still-missing facts: {want}.\n"
        "Go straight to the authoritative parcel record — the county/city assessor or tax record. For "
        "NYC search the BBL on PropertyShark / ACRIS / NYC DOF and use StreetEasy for a unit's "
        "beds/baths/interior sqft. Report each fact with its source. If a fact truly cannot be found, "
        "use 'Information not available' — do not guess."
    )


def research_property(
    address: str,
    anthropic_api_key: str,
    owner_name: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    effort: str = "low",
    max_searches: int = 8,
    max_fetches: int = 2,
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

        # Pass 1: full research + structuring.
        research_text = _run_search(_research_prompt(address, owner_name), max_searches, max_fetches)
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
        if address_resolves and property_kind == "residential":
            missing = [f for f in _CORE_FIELDS if _field(data, f) == "Information not available"]
            elapsed = time.monotonic() - _start
            if missing and elapsed > _GAPFILL_SKIP_AFTER:
                logger.info("Skipping gap-fill for '%s' — pass 1 took %.0fs (>%.0fs), staying under the worker window",
                            address, elapsed, _GAPFILL_SKIP_AFTER)
                missing = []
            if missing:
                logger.info("Gap-fill pass for '%s' (missing: %s)", address, ", ".join(missing))
                try:
                    gap_text = _run_search(_gap_prompt(address, missing), 4, 1)
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
