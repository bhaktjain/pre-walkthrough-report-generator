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
        "zoning", "flood_zone", "neighborhood", "feasibility_notes",
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
        "zoning": {"type": "string", "description": "zoning district + key setback/lot-coverage limits if found"},
        "flood_zone": {"type": "string", "description": "FEMA flood zone designation"},
        "neighborhood": {"type": "string"},
        "feasibility_notes": {
            "type": "array", "items": {"type": "string"},
            "description": "renovation-relevant facts: sewer vs septic signal, additions/permits on record, lot-coverage headroom, flood implications, etc.",
        },
        "owner_summary": {
            "type": "string",
            "description": "Ownership confirmation from the public deed/tax record, plus any PUBLIC, professionally-relevant context. Do NOT include personal, financial, family, or social-media details.",
        },
        "sources": {"type": "array", "items": {"type": "string", "description": "source URL"}},
    },
}


def _research_prompt(address: str, owner_name: Optional[str]) -> str:
    owner_line = (
        f"\nThe owner on file may be: {owner_name}. Confirm current ownership from the public deed/tax "
        "record and how long they have owned the home. Then gather PUBLIC, professionally-relevant "
        "context that helps the salesperson build rapport and gauge project scope/budget: the owner's "
        "profession, employer or business, public professional profiles (LinkedIn, company site, "
        "professional bios), and any other properties they own per public records. "
        "Do NOT compile private personal information: no personal finances/income/net-worth estimates, "
        "no family or household details beyond what is already known, and no social-media or personal-life "
        "profiling. Stick to public professional and property-record information."
        if owner_name else
        "\nIdentify the current owner of record from the public deed/tax record, and note any public "
        "professional profile (profession, employer/business) that helps tailor a renovation proposal. "
        "Public professional and property-record information only — no personal/financial/family/social digging."
    )
    return (
        f"You are preparing an internal pre-walkthrough research brief for a renovation contractor's "
        f"salesperson. Research the residential property at:\n\n    {address}\n\n"
        "Use web search and fetch authoritative PUBLIC sources — the county tax assessor / property "
        "records, state parcel/GIS databases (e.g. njparcels, njpropertyrecords, county GIS), the FEMA "
        "flood map, the municipal zoning code, and Zillow/Redfin/Realtor public listing pages for "
        "historical facts. Cross-check across sources and prefer the county/assessor record for facts.\n\n"
        "Find: beds, baths, living-area square footage, year built, property type, lot size, last sale "
        "price & date, assessed value, zoning district (with setback/lot-coverage limits if available), "
        "and FEMA flood zone. Also surface renovation-relevant feasibility facts: municipal sewer vs. "
        "septic, any additions/permits on record, and whether the lot has room to build out within the "
        "zoning envelope."
        + owner_line +
        "\n\nBe factual and cite your sources. If a fact cannot be found, say so rather than guessing."
    )


def research_property(
    address: str,
    anthropic_api_key: str,
    owner_name: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    effort: str = "low",
    max_searches: int = 5,
    max_fetches: int = 1,
    use_thinking: bool = False,
    timeout: float = 260.0,
) -> Optional[Dict[str, Any]]:
    """Research a property (and lightly, its owner) from public web sources.

    HARD-BOUNDED for the report pipeline: basic web search (no dynamic-filtering
    code-exec), no page fetches, no extended thinking, a strict per-call client
    timeout, and a 2-call cap. Deep runs (page fetches, thinking, more searches)
    are minutes-to-tens-of-minutes long and are NOT used here — pass richer args
    explicitly for an offline dossier.

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
            model=model, max_tokens=4000,
            output_config={"effort": effort},
            tools=tools,
        )
        if use_thinking:
            create_kwargs["thinking"] = {"type": "adaptive"}
        messages = [{"role": "user", "content": _research_prompt(address, owner_name)}]
        response = None
        for _ in range(2):  # at most one pause_turn continuation
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
            model=model, max_tokens=3000,
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
        data = json.loads(raw)

        def _v(key: str) -> str:
            val = str(data.get(key) or "").strip()
            return val if val else "Information not available"

        property_details = {
            "address": address,
            "price": _v("last_sale_price"),
            "last_sold_price": _v("last_sale_price"),
            "last_sold_date": _v("last_sale_date"),
            "bedrooms": _v("bedrooms"),
            "bathrooms": _v("bathrooms"),
            "sqft": _v("sqft"),
            "year_built": _v("year_built"),
            "property_type": _v("property_type"),
            "lot_size": _v("lot_size"),
            "assessed_value": _v("assessed_value"),
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
