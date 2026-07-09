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
        "found", "bedrooms", "bathrooms", "sqft", "year_built", "property_type",
        "lot_size", "last_sale_price", "last_sale_date", "assessed_value",
        "property_taxes", "zoning", "flood_zone", "neighborhood", "feasibility_notes",
        "owner_summary", "sources",
    ],
    "properties": {
        "found": {"type": "boolean", "description": "true only if THIS specific property was identified in public records"},
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
        "salesperson, who will meet the homeowner at the property. Be THOROUGH and specific — this brief "
        "should let the rep walk in fully informed. Research the residential property at:\n\n"
        f"    {address}\n\n"
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

    Returns {property_details, feasibility, owner_summary, sources, found} or
    None on any failure/timeout. Never raises.
    """
    if anthropic is None or not anthropic_api_key or not address:
        logger.info("Property research skipped (no SDK / key / address)")
        return None
    try:
        # Hard client-side timeout + no retries so one report can't hang for
        # tens of minutes on a slow search loop.
        client = anthropic.Anthropic(api_key=anthropic_api_key, timeout=timeout, max_retries=0)

        # Basic web search is much faster than the _20260209 (dynamic-filtering)
        # variant. Page fetches are the slowest part, so they default off.
        tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": max_searches}]
        if max_fetches > 0:
            tools.append({"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": max_fetches})
        create_kwargs = dict(
            model=model, max_tokens=6000,
            output_config={"effort": effort},
            tools=tools,
        )
        if use_thinking:
            create_kwargs["thinking"] = {"type": "adaptive"}
        messages = [{"role": "user", "content": _research_prompt(address, owner_name)}]
        response = None
        for _ in range(4):  # allow a few pause_turn continuations for the deeper search/fetch rounds
            response = client.messages.create(messages=messages, **create_kwargs)
            if response.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})
                continue
            break
        research_text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
        if not research_text.strip():
            logger.info("Property research produced no text for '%s'", address)
            return None

        # 2. Structure the findings (separate call — no tools, so output_config.format is clean).
        struct = client.messages.create(
            model=model, max_tokens=6000,  # ample headroom so the JSON isn't truncated
            messages=[{
                "role": "user",
                "content": (
                    "Extract the property research below into the required JSON. Use the exact string "
                    "'Information not available' for any field the research did not establish. Do not "
                    "invent values.\n\n--- RESEARCH ---\n" + research_text
                ),
            }],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": _RESEARCH_SCHEMA}},
        )
        raw = next((b.text for b in struct.content if getattr(b, "type", None) == "text"), "")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Salvage a slow, already-successful research run whose structuring
            # JSON came back wrapped in prose/markdown — grab the outermost {...}
            # rather than discarding everything. Genuinely truncated JSON still
            # fails here and degrades gracefully via the outer handler.
            import re as _re
            m = _re.search(r"\{.*\}", raw, _re.DOTALL)
            if not m:
                logger.warning("Property research structuring returned unparseable JSON for '%s'", address)
                return None
            data = json.loads(m.group(0))

        def _v(key: str) -> str:
            val = str(data.get(key) or "").strip()
            return val if val else "Information not available"

        property_details = {
            "address": address,
            # This pipeline researches OWNED (off-market) homes — there is no
            # active list price, so leave 'price' as the sentinel. The document
            # generator then renders the sale under a "Last Sold Price" label
            # instead of mislabeling a years-old purchase as the current price.
            "price": "Information not available",
            "last_sold_price": _v("last_sale_price"),
            "last_sold_date": _v("last_sale_date"),
            "bedrooms": _v("bedrooms"),
            "bathrooms": _v("bathrooms"),
            "sqft": _v("sqft"),
            "year_built": _v("year_built"),
            "property_type": _v("property_type"),
            "lot_size": _v("lot_size"),
            "assessed_value": _v("assessed_value"),
            "property_taxes": _v("property_taxes"),
            "neighborhood": _v("neighborhood"),
            "photos": [],
            "floor_plans": [],
            "source": "public records research",
        }
        return {
            "found": bool(data.get("found")),
            "property_details": property_details,
            "zoning": _v("zoning"),
            "flood_zone": _v("flood_zone"),
            "feasibility": [s for s in (data.get("feasibility_notes") or []) if str(s).strip()],
            "owner_summary": _v("owner_summary"),
            "sources": [s for s in (data.get("sources") or []) if str(s).strip()],
        }
    except Exception as e:  # never break the pipeline
        logger.warning("Property research failed for '%s': %s", address, e)
        return None
