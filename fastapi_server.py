from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Depends, Request
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import tempfile
import os
import uuid
import time
import threading
import sys
import copy
import hmac
from pathlib import Path
from typing import Optional
import logging
import asyncio
import json
import re
from config_manager import config_manager
from datetime import datetime
from pydantic import BaseModel

# Add the pre_walkthrough_generator to the path
sys.path.append(str(Path(__file__).parent / "pre_walkthrough_generator" / "src"))

# Import the pipeline modules directly (sys.path includes the src dir above).
# Fail fast on any import/config error rather than starting a half-initialized
# app that 500s at request time.
try:
    import config
    import transcript_processor
    import property_api
    import document_generator
    from neighboring_projects import NeighboringProjectsManager
except ImportError as e:
    logging.error(f"Import error: {e}")
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pre-Walkthrough Report Generator API",
    description="API for generating pre-walkthrough reports from transcripts",
    version="1.0.0"
)

# Track server metrics
server_metrics = {
    "start_time": datetime.now(),
    "requests_processed": 0,
    "errors": 0,
    "last_request": None
}

# --- Admin auth, upload limits, and secret redaction -------------------------
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", 10 * 1024 * 1024))  # 10 MB
ALLOWED_TRANSCRIPT_EXTS = {".txt", ".json", ".jsonl", ".md", ".docx", ".pdf"}
ALLOWED_TEMPLATE_EXTS = {".docx"}


def require_admin(x_admin_key: Optional[str] = Header(default=None)):
    """Gate admin endpoints behind a shared secret (env ADMIN_API_KEY).

    Fail-closed: if ADMIN_API_KEY is not configured the endpoints are disabled,
    so config/secrets are never exposed by default.
    """
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=503, detail="Admin endpoints are disabled (set ADMIN_API_KEY to enable).")
    if not x_admin_key or not hmac.compare_digest(x_admin_key, ADMIN_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing admin key.")
    return True


def _redact_config(cfg) -> dict:
    """Deep-copy the config with all secret values masked."""
    try:
        redacted = copy.deepcopy(cfg)
    except Exception:
        return {"error": "config unavailable"}
    api_keys = redacted.get("api_keys") if isinstance(redacted, dict) else None
    if isinstance(api_keys, dict):
        def _mask(v):
            if isinstance(v, dict):
                return {k: _mask(sv) for k, sv in v.items()}
            return "***redacted***" if v else ""
        redacted["api_keys"] = {k: _mask(v) for k, v in api_keys.items()}
    return redacted

# Keep the Zoho deals cache current without a redeploy. The service stays up
# for days, so a startup-only sync isn't enough — we also refresh on a timer.
ZOHO_REFRESH_INTERVAL_HOURS = 48


def _sync_zoho_cache(force: bool = False) -> bool:
    """Refresh the Zoho deals cache from CRM. Returns True if it refreshed.

    Blocking (network + geocoding) — call via ``asyncio.to_thread`` from async
    code. Existing neighborhood tags are carried forward (matched by Deal_Name),
    so only newly added deals are geocoded and the refresh stays fast.
    """
    manager = NeighboringProjectsManager()
    stats = manager.get_cache_stats()
    if not force and stats.get('valid') and stats.get('count', 0) > 0:
        logger.info(f"Zoho cache is valid ({stats['count']} deals, {stats.get('age_hours', 0):.1f}h old). Skipping sync.")
        return False

    # Credentials come from the environment first, then config.json (via Config).
    cfg = config.Config()
    zoho_client_id = os.environ.get("ZOHO_CLIENT_ID") or cfg.zoho_client_id
    zoho_client_secret = os.environ.get("ZOHO_CLIENT_SECRET") or cfg.zoho_client_secret
    zoho_refresh_token = os.environ.get("ZOHO_REFRESH_TOKEN") or cfg.zoho_refresh_token
    if not all([zoho_client_id, zoho_client_secret, zoho_refresh_token]):
        logger.warning("Zoho credentials not configured. Neighboring projects will use existing cache if available.")
        return False

    logger.info("Syncing Zoho deals%s...", " (forced)" if force else "")
    from zoho_api import ZohoAPI
    from nyc_neighborhoods import enrich_deals_with_neighborhoods
    zoho = ZohoAPI(zoho_client_id, zoho_client_secret, zoho_refresh_token)
    fields = ["Deal_Name", "Amount", "Stage", "Contact_Name", "Closing_Date"]
    deals = zoho.get_all_records("Deals", fields=fields, max_records=5000)
    if not deals:
        logger.warning("No deals returned from Zoho API")
        return False

    # Carry forward existing tags (modifies `deals` in place), then geocode only
    # the deals still untagged — i.e. the newly added ones.
    manager.save_cache(deals, preserve_neighborhoods=True)
    new_deals = [d for d in deals if not d.get("Neighborhood")]
    if new_deals:
        enrich_deals_with_neighborhoods(new_deals, use_geocoding=True)
        manager.save_cache(deals, preserve_neighborhoods=True)
    tagged = sum(1 for d in deals if d.get("Neighborhood"))
    logger.info(f"Zoho cache refreshed: {len(deals)} deals ({tagged} tagged, {len(new_deals)} newly geocoded)")
    return True


async def _periodic_zoho_refresh():
    """Force a Zoho cache refresh every ZOHO_REFRESH_INTERVAL_HOURS."""
    while True:
        await asyncio.sleep(ZOHO_REFRESH_INTERVAL_HOURS * 3600)
        try:
            await asyncio.to_thread(_sync_zoho_cache, True)
        except Exception as e:
            logger.error(f"Periodic Zoho refresh failed (non-fatal): {e}")


@app.on_event("startup")
async def startup_sync_zoho_cache():
    """Refresh the Zoho cache if stale on startup, then keep it fresh on a timer."""
    try:
        await asyncio.to_thread(_sync_zoho_cache, False)
    except Exception as e:
        logger.error(f"Startup Zoho sync failed (non-fatal): {e}")
    # Keep neighboring-project data current between deploys.
    asyncio.create_task(_periodic_zoho_refresh())


@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    uptime = datetime.now() - server_metrics["start_time"]
    # Non-secret integration flags (booleans only) so we can confirm which creds
    # are actually configured on this deployment.
    try:
        _cfg = config.Config()
        integrations = {
            "zoho_configured": _cfg.has_zoho,
            "anthropic_configured": bool(_cfg.anthropic_api_key),
        }
    except Exception as e:
        integrations = {"error": type(e).__name__}
    return {
        "status": "healthy",
        "uptime_seconds": uptime.total_seconds(),
        "requests_processed": server_metrics["requests_processed"],
        "errors": server_metrics["errors"],
        "last_request": server_metrics["last_request"],
        "integrations": integrations,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics")
async def get_metrics(_: bool = Depends(require_admin)):
    """Get detailed server metrics (admin only; secrets redacted)"""
    return {
        "server_metrics": server_metrics,
        "config": _redact_config(config_manager.config),
        "memory_usage": "Available via system monitoring"
    }

def clean_transcript(raw_transcript: str) -> str:
    """Clean the transcript text"""
    transcript = raw_transcript.strip()
    return transcript

def clean_address(address: str) -> str:
    """Clean and standardize address format"""
    address = ' '.join(address.split())
    address = re.sub(r'(?i)\b(apartment|apt\.?|unit)\s*#?\s*(\w+)', r'Apt \2', address)
    # Only expand abbreviations that are clearly street names, not state abbreviations
    # Use word boundaries and context to avoid changing state abbreviations
    abbr = {
        r'\b(\d+\s+\w+\s+)Pl\b\.?' : r'\1Place',  # Only expand Pl when it's clearly a street
        r'\b(\d+\s+\w+\s+)St\b\.?' : r'\1Street',  # Only expand St when it's clearly a street
        r'\b(\d+\s+\w+\s+)Ave\b\.?' : r'\1Avenue',
        r'\b(\d+\s+\w+\s+)Rd\b\.?' : r'\1Road',
        r'\bPkwy\b\.?' : 'Parkway'
        # Don't expand Ct as it could be Connecticut
    }
    for pat, repl in abbr.items():
        address = re.sub(pat, repl, address, flags=re.IGNORECASE)
    return address

def process_transcript_and_generate_report(transcript_path: str, address: str = None, last_name: str = None, output_name: str = None) -> str:
    """
    Process a transcript and generate a pre-walkthrough report.
    
    Args:
        transcript_path: Path to the transcript file
        address: Property address (optional, will be extracted from transcript if not provided)
        last_name: Last name for the report (optional)
    
    Returns:
        Path to the generated report file
    """
    try:
        # Initialize components
        config_obj = config.Config()
        doc_generator = document_generator.DocumentGenerator()
        transcript_processor_obj = transcript_processor.TranscriptProcessor(config_obj.anthropic_api_key, config_obj.claude_model)

        # Read and clean transcript
        with open(transcript_path, 'r') as f:
            transcript = clean_transcript(f.read())
        
        logger.info(f"Processing transcript: {transcript_path} ({len(transcript)} chars)")

        # Extract transcript information
        transcript_info = transcript_processor_obj.extract_info(transcript)
        logger.info("Transcript processed successfully")
        
        # Validate that we have meaningful data to generate a report
        if not transcript_info or not any([
            transcript_info.get('property_address'),
            transcript_info.get('client_info', {}).get('names'),
            transcript_info.get('renovation_scope', {}).get('kitchen', {}).get('description'),
            transcript_info.get('renovation_scope', {}).get('bathrooms', {}).get('specific_requirements'),
            transcript_info.get('renovation_scope', {}).get('additional_work', {}).get('rooms')
        ]):
            logger.warning("No meaningful consultation data found in transcript")
            logger.warning("Transcript preview (first 300 chars): %r", transcript[:300])
            raise Exception("The provided transcript does not contain sufficient consultation information to generate a meaningful report. Please provide a transcript from a renovation consultation that includes project details, client information, or scope of work.")

        # Use provided address first, then check transcript_info, then extract separately
        if address:
            logger.info(f"Using provided address: {address}")
        else:
            # Check if address was extracted in transcript_info
            transcript_address = transcript_info.get('property_address')
            if transcript_address and transcript_address.strip() and transcript_address.upper() != 'NONE':
                address = transcript_address
                logger.info(f"Using address from transcript info: {address}")
            else:
                logger.info("No address in transcript info, extracting separately...")
                address = transcript_processor_obj.extract_address(transcript)
                if address and address.upper() != 'NONE':
                    logger.info(f"Extracted address from transcript: {address}")
                else:
                    logger.info("Could not extract address from transcript, trying filename...")
                    # Try to match any plausible address substring
                    fname = Path(transcript_path).stem.replace('_', ' ').replace('-', ' ')
                    m = re.search(r"(\d+\s*[NSEWnsew]?\s*\d*\s*\w+\s*(?:st|street|ave|avenue|rd|road|blvd|drive|dr|pl|place)?[^,\n]*)(?:,?\s*(apt|apartment|unit)?\s*([\w\d]+))?", fname, re.IGNORECASE)
                    if m:
                        street = m.group(1).strip()
                        apt = m.group(3)
                        city = "Brooklyn"
                        state = "NY"
                        addr = f"{street}"
                        if apt:
                            addr += f", Apt {apt}"
                        addr += f", {city}, {state}"
                        address = addr
                        logger.info(f"Constructed address from filename: {address}")
                    else:
                        address = fname + ", Brooklyn, NY"
                    logger.info(f"Using fallback address: {address}")
        
        if address:
            address = clean_address(address)
            # Only add Brooklyn, NY if the address doesn't already have a city, state
            # Check if address already has a proper city, state format
            if not re.search(r",\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}", address):
                # Only add if it looks like a street address without city/state
                if re.match(r"\d+\s*[NSEW]?\s*\d*\s*\w+\s*(st|street|ave|avenue|rd|road|blvd|drive|dr|pl|place)", address, re.IGNORECASE):
                    if not re.search(r",\s*(brooklyn|manhattan|queens|bronx|new york|ny|nyc|nj|jersey|miami|fl|florida|ct|connecticut|westchester)", address, re.IGNORECASE):
                        address += ", Brooklyn, NY"

        logger.info(f"Using address: {address}")
        # Flag up front when the address isn't a specific parcel (no leading street
        # number — e.g. a park or place-name). Property records won't apply; the
        # research classifies it and the report self-explains the empty details.
        if address and not re.match(r'^\s*(?:apt\.?\s*\w+\s*,?\s*)?\d', address, re.IGNORECASE):
            logger.warning("Address %r does not begin with a numeric street number — if it is a park, "
                           "landmark, or general area (not an individual parcel), Property Details will "
                           "be limited (the research classifies this and the report self-explains).", address)

        # --- Property + owner research via Claude web search (PRIMARY source) ---
        # Realtor/SerpAPI only cover ON-market listings, so owned homes (the
        # typical walkthrough client) come back empty. Public-records web research
        # fills the report instead. This is the slow step (minutes) — the async
        # endpoints exist so callers don't hit an HTTP timeout waiting for it.
        import property_research
        owner_name = None
        names = (transcript_info.get('client_info') or {}).get('names') or []
        if names:
            owner_name = str(names[0]).split('(')[0].strip() or None

        # Strengthen the identity for owner research: the transcript often yields
        # only a FIRST name, but the request's last_name comes from Zoho (the deal
        # contact). If the transcript name is a single token and doesn't already
        # include that surname, combine them into a fuller, more-verifiable name.
        if last_name and str(last_name).strip():
            ln = str(last_name).strip()
            tokens = (owner_name or '').split()
            if not owner_name:
                owner_name = ln
            elif len(tokens) < 2 and ln.lower() not in owner_name.lower():
                owner_name = f"{tokens[0]} {ln}"
            logger.info("Owner identity for research: %r (transcript + Zoho last_name)", owner_name)

        # Client-provided contact details (from the consultation) help the research
        # confirm WHICH public professional profile is the right person for a common
        # name — used only to pin professional identity, not for personal profiling.
        _ci = transcript_info.get('client_info') or {}
        owner_email = (_ci.get('email') or '').strip() or None
        owner_phone = (_ci.get('phone') or '').strip() or None

        # --- Zoho CONTACT record = source of truth for WHO the walkthrough is with ---
        # The property address lives on the contact's Mailing_Street, so this matches
        # reliably. It corrects cases where the transcript surfaced the wrong name
        # (e.g. the SELLER of an in-contract unit) and adds authoritative
        # status/budget/sqft. (Deal notes stay off — this is identity only.)
        zoho_contact = {}
        client_context = None
        try:
            if config_obj.has_zoho:  # property, not a method
                from zoho_api import ZohoAPI
                zoho_contact = ZohoAPI(
                    config_obj.zoho_client_id, config_obj.zoho_client_secret,
                    config_obj.zoho_refresh_token,
                ).get_contact_by_address(address, owner_name) or {}
        except Exception as e:
            logger.error("Zoho contact lookup failed: %s", e)
        if zoho_contact.get("full_name"):
            owner_name = zoho_contact["full_name"]          # authoritative client identity
            owner_email = zoho_contact.get("email") or owner_email
            owner_phone = zoho_contact.get("phone") or owner_phone
            logger.info("Using Zoho contact as authoritative client: %r (status=%r)",
                        owner_name, zoho_contact.get("property_status"))
        # In-contract framing: the contact is the incoming BUYER, not the deed seller.
        _status = (zoho_contact.get("property_status") or "").lower()
        if "contract" in _status or "purchas" in (zoho_contact.get("description") or "").lower():
            client_context = (
                f"IMPORTANT: per the CRM, {owner_name or 'the client'} is the INCOMING BUYER / new owner "
                "of this unit (it is IN CONTRACT / being purchased). Research and describe THIS person as "
                "the buyer. The public deed/tax record will still show the CURRENT owner (the SELLER) — do "
                "not confuse the two; if you mention the deed owner, label them the seller."
            )

        logger.info("Researching property + owner via web search for '%s' (may take a few minutes)...", address)
        research = property_research.research_property(
            address, config_obj.anthropic_api_key, owner_name=owner_name,
            owner_email=owner_email, owner_phone=owner_phone, client_context=client_context,
        ) or {}
        property_details = research.get("property_details") or {}
        # Backfill authoritative Zoho facts the web research may have missed.
        if isinstance(property_details, dict) and zoho_contact:
            if zoho_contact.get("sq_ft") and str(property_details.get("sqft") or "").strip() in ("", "Information not available"):
                property_details["sqft"] = f"{zoho_contact['sq_ft']} sq ft (per CRM)"
        if not property_details:
            logger.warning("Property research returned nothing for '%s' — limited property info", address)
        else:
            logger.info("Property research complete (found=%s)", research.get("found"))

        # --- Neighboring projects from the Zoho cache ---
        logger.info("Looking up neighboring projects...")
        neighboring_projects = []
        try:
            projects_manager = NeighboringProjectsManager()
            neighborhood = property_details.get('neighborhood') if isinstance(property_details, dict) else None
            if neighborhood == 'Information not available':
                neighborhood = None
            neighboring_projects = projects_manager.find_neighboring_projects(
                target_address=address,
                target_neighborhood=neighborhood,
                same_building_only=False,
            )
            logger.info(f"Found {len(neighboring_projects)} neighboring projects")
        except Exception as e:
            logger.error(f"Error fetching neighboring projects: {e}")

        # --- Matching deal's CRM notes (best-effort) ---
        # CRM notes temporarily DISABLED per request. Leaving zoho_notes empty
        # makes the report's "CRM Notes" section self-suppress (see
        # _add_crm_notes). Re-enable by un-commenting the fetch below.
        zoho_notes = []
        # try:
        #     zc = (os.environ.get("ZOHO_CLIENT_ID") or config_obj.zoho_client_id,
        #           os.environ.get("ZOHO_CLIENT_SECRET") or config_obj.zoho_client_secret,
        #           os.environ.get("ZOHO_REFRESH_TOKEN") or config_obj.zoho_refresh_token)
        #     if all(zc):
        #         from zoho_api import ZohoAPI
        #         zoho_notes = ZohoAPI(*zc).get_relevant_notes(address=address, contact_name=owner_name)
        # except Exception as e:
        #     logger.error(f"Error fetching CRM notes: {e}")

        # --- Assemble report data ---
        final_data = {
            "property_address": address,
            "property_id": research.get("property_id"),
            "realtor_url": None,
            "zillow_url": None,
            "property_details": property_details,
            "images": {"images": []},
            "floor_plans": {"floor_plans": []},
            "transcript_info": transcript_info,
            "neighboring_projects": neighboring_projects,
            "research_zoning": research.get("zoning"),
            "research_flood": research.get("flood_zone"),
            "research_feasibility": research.get("feasibility") or [],
            "research_sources": research.get("sources") or [],
            "owner_summary": research.get("owner_summary"),
            "research_address_resolves": research.get("address_resolves", True),
            "research_property_kind": research.get("property_kind"),
            "zoho_contact": zoho_contact,
            "zoho_notes": zoho_notes,
        }

        # Generate report
        logger.info("Generating pre-walkthrough report...")
        
        # Sanitize address for filename - remove invalid characters
        def sanitize_filename(text: str) -> str:
            """Remove or replace invalid filename characters"""
            # Replace invalid characters with underscore
            invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '#']
            for char in invalid_chars:
                text = text.replace(char, '_')
            # Replace multiple underscores with single
            while '__' in text:
                text = text.replace('__', '_')
            # Remove leading/trailing underscores
            return text.strip('_')
        
        safe_addr = sanitize_filename(address.split(',')[0]) if address else Path(transcript_path).stem
        safe_addr = safe_addr.replace(' ', '_')
        
        if output_name:
            # Async jobs pass a unique name so concurrent/repeated reports never
            # collide on the same data/ file (which could serve one client another's report).
            file_name = f"{sanitize_filename(output_name)}.docx"
        elif last_name:
            safe_last_name = sanitize_filename(last_name)
            file_name = f"PreWalk_{safe_last_name}.docx"
        else:
            file_name = f"PreWalk_{safe_addr}.docx"
        
        # Report output dir is env-configurable so it can point at a mounted
        # persistent disk (with REPORT_JOBS_DIR) for durability across redeploys.
        output_dir = os.environ.get("REPORT_OUTPUT_DIR") or "data"
        output_path = doc_generator.generate_report(final_data, output_dir=output_dir, file_name=file_name)
        
        if not output_path:
            raise Exception("Failed to generate report")
        
        logger.info(f"Report generated successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error in process_transcript_and_generate_report: {str(e)}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Pre-Walkthrough Report Generator API is running"}

@app.post("/generate-report")
async def generate_report(
    transcript_file: UploadFile = File(...),
    address: str = None,
    last_name: str = None
):
    """
    Generate a pre-walkthrough report from a transcript file.
    
    Args:
        transcript_file: The transcript file (txt, docx, pdf)
        address: Property address (optional, will be extracted from transcript if not provided)
        last_name: Last name for the report (optional)
    
    Returns:
        The generated DOCX report file
    """
    try:
        server_metrics["requests_processed"] += 1
        server_metrics["last_request"] = datetime.now().isoformat()
        logger.info(f"Received request to generate report for file: {transcript_file.filename}")
        
        # Validate the upload (size + extension) before persisting it.
        content = await transcript_file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Transcript file too large.")
        safe_name = os.path.basename(transcript_file.filename or "transcript")
        ext = Path(safe_name).suffix.lower()
        if ext and ext not in ALLOWED_TRANSCRIPT_EXTS:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {ext}")

        # Create a temporary file to save the uploaded transcript
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{safe_name}") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"Saved transcript to temporary file: {temp_file_path}")
        
        # Generate the report
        report_path = process_transcript_and_generate_report(
            transcript_path=temp_file_path,
            address=address,
            last_name=last_name
        )
        
        # Clean up the temporary transcript file
        os.unlink(temp_file_path)
        
        if not report_path or not os.path.exists(report_path):
            raise HTTPException(status_code=500, detail="Failed to generate report")
        
        logger.info(f"Report generated successfully: {report_path}")
        
        # Return the generated report file
        return FileResponse(
            path=report_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"PreWalkReport_{last_name or 'Report'}.docx"
        )
        
    except HTTPException:
        # Propagate intended HTTP errors (413/415/etc.) unchanged.
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise
    except Exception as e:
        server_metrics["errors"] += 1
        logger.error(f"Error generating report: {str(e)}")
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

class TranscriptRequest(BaseModel):
    transcript_text: str
    address: str = None
    last_name: str = None

def flatten_jsonl_transcript(transcript_text: str) -> str:
    """Convert JSONL transcript (if detected) to plain text, else return as-is."""
    lines = transcript_text.strip().splitlines()
    parsed_lines = []
    for line in lines:
        try:
            obj = json.loads(line)
            # If the object is {"": "Speaker: text"}, extract the value
            if isinstance(obj, dict) and "" in obj:
                parsed_lines.append(obj[""])
            else:
                parsed_lines.append(str(obj))
        except Exception:
            # Not JSON, treat as plain text
            parsed_lines.append(line)
    return "\n".join(parsed_lines)

@app.post("/generate-report-from-text")
async def generate_report_from_text(request: TranscriptRequest):
    """
    Generate a pre-walkthrough report from transcript text.
    
    Args:
        transcript_text: The transcript text content
        address: Property address (optional, will be extracted from transcript if not provided)
        last_name: Last name for the report (optional)
    
    Returns:
        The generated DOCX report file
    """
    try:
        logger.info("Received request to generate report from text")
        
        # Validate transcript content
        if not request.transcript_text or not request.transcript_text.strip():
            logger.error("Empty or missing transcript text")
            raise HTTPException(status_code=400, detail="Transcript text is required and cannot be empty")
        
        # Flatten JSONL if needed
        flattened = flatten_jsonl_transcript(request.transcript_text)
        
        # Additional validation after flattening
        if not flattened or not flattened.strip():
            logger.error("Transcript text is empty after processing")
            raise HTTPException(status_code=400, detail="Transcript text appears to be empty or invalid")
        
        # Check if transcript has meaningful content (not just whitespace/formatting)
        meaningful_content = re.sub(r'[{}":\s\n\r]', '', flattened)
        if len(meaningful_content) < 50:  # Arbitrary threshold for meaningful content
            logger.error(f"Transcript appears to have insufficient content: {len(meaningful_content)} characters")
            raise HTTPException(status_code=400, detail="Transcript text appears to have insufficient content for report generation")
        
        # Create a temporary file with the transcript text
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w') as temp_file:
            temp_file.write(flattened)
            temp_file_path = temp_file.name
        logger.info(f"Saved transcript text to temporary file: {temp_file_path}")
        
        # Generate the report
        report_path = process_transcript_and_generate_report(
            transcript_path=temp_file_path,
            address=request.address,
            last_name=request.last_name
        )
        # Clean up the temporary transcript file
        os.unlink(temp_file_path)
        if not report_path or not os.path.exists(report_path):
            raise HTTPException(status_code=500, detail="Failed to generate report")
        logger.info(f"Report generated successfully: {report_path}")
        # Return the generated report file
        return FileResponse(
            path=report_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"PreWalkReport_{request.last_name or 'Report'}.docx"
        )
    except HTTPException:
        # Propagate intended HTTP errors (400/etc.) unchanged.
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

# --- Async report generation -------------------------------------------------
# Deep property research runs for several minutes, longer than a sync HTTP step
# will wait. These endpoints implement the standard 202 + Location poll pattern:
# POST returns 202 immediately with a Location; poll that Location until it
# returns the .docx. In Power Automate, turn ON the HTTP action's "Asynchronous
# pattern" and it handles the polling automatically. Single gunicorn worker, so
# the in-memory job store is shared across the POST and the poll requests.
_report_jobs: dict = {}
_REPORT_JOB_TTL = 3600   # seconds a finished job (and its .docx) is retained
_REPORT_JOB_MAX = 200    # hard cap on retained jobs
# A finished job's metadata is also written to disk so a report that COMPLETED
# survives a worker recycle: report_status recovers it after the in-memory store
# is lost, instead of 404-ing. (A full container redeploy still wipes ephemeral
# disk — point REPORT_JOBS_DIR at a mounted persistent disk to survive deploys.)
_JOBS_META_DIR = os.environ.get("REPORT_JOBS_DIR") or os.path.join(tempfile.gettempdir(), "prewalk_jobs")


def _valid_job_id(job_id: str) -> bool:
    """job_id is a uuid4 hex — reject anything else before it touches the fs."""
    return bool(re.fullmatch(r'[0-9a-fA-F]{32}', job_id or ''))


def _job_meta_path(job_id: str) -> str:
    return os.path.join(_JOBS_META_DIR, f"{job_id}.json")


def _persist_job(job_id: str, rec: dict) -> None:
    """Write a finished job's metadata to disk (best-effort, atomic replace)."""
    try:
        os.makedirs(_JOBS_META_DIR, exist_ok=True)
        tmp = _job_meta_path(job_id) + ".tmp"
        with open(tmp, "w") as f:
            json.dump(rec, f)
        os.replace(tmp, _job_meta_path(job_id))
    except Exception as e:
        logger.warning("Could not persist job %s metadata: %s", job_id, e)


def _load_job(job_id: str) -> Optional[dict]:
    """Recover a finished job's metadata from disk after an in-memory miss."""
    if not _valid_job_id(job_id):
        return None
    try:
        with open(_job_meta_path(job_id)) as f:
            return json.load(f)
    except Exception:
        return None


def _remove_job_files(path: Optional[str], job_id: str) -> None:
    """Delete a finished job's report .docx and its on-disk metadata sidecar."""
    targets = [path]
    if _valid_job_id(job_id):
        targets.append(_job_meta_path(job_id))
    for p in targets:
        if p and os.path.exists(p):
            try:
                os.unlink(p)
            except Exception:
                pass


def _prune_report_jobs() -> None:
    """Evict finished jobs (deleting their .docx + metadata sidecar) past the TTL
    or beyond the cap, so the long-lived worker doesn't leak memory/disk. Also
    sweeps orphaned on-disk sidecars left by a previous worker."""
    try:
        now = time.time()
        finished = [(jid, j) for jid, j in _report_jobs.items() if j.get("status") in ("done", "error")]
        stale = {jid for jid, j in finished if now - j.get("ts", now) > _REPORT_JOB_TTL}
        remaining = [(jid, j) for jid, j in finished if jid not in stale]
        overflow = len(_report_jobs) - len(stale) - _REPORT_JOB_MAX
        if overflow > 0:
            for jid, _ in sorted(remaining, key=lambda kv: kv[1].get("ts", 0))[:overflow]:
                stale.add(jid)
        for jid in stale:
            j = _report_jobs.pop(jid, None)
            _remove_job_files((j or {}).get("path"), jid)
        # Sweep on-disk sidecars past the TTL (orphans from a prior worker whose
        # in-memory store is gone), so persisted jobs don't accumulate forever.
        try:
            for fn in os.listdir(_JOBS_META_DIR):
                if not fn.endswith(".json"):
                    continue
                jid = fn[:-5]
                if jid in _report_jobs:
                    continue
                rec = _load_job(jid) or {}
                if now - float(rec.get("ts", 0) or 0) > _REPORT_JOB_TTL:
                    _remove_job_files(rec.get("path"), jid)
        except FileNotFoundError:
            pass
    except Exception as e:
        logger.warning("Report-job prune failed: %s", e)


def _run_report_job(job_id: str, flattened: str, address: Optional[str], last_name: Optional[str]) -> None:
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w") as temp_file:
            temp_file.write(flattened)
            temp_file_path = temp_file.name
        report_path = process_transcript_and_generate_report(
            transcript_path=temp_file_path, address=address, last_name=last_name,
            output_name=f"PreWalk_{job_id}",  # unique on-disk name per job
        )
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        if not report_path or not os.path.exists(report_path):
            rec = {"status": "error", "error": "Failed to generate report", "ts": time.time()}
        else:
            rec = {"status": "done", "path": report_path, "last_name": last_name, "ts": time.time()}
            logger.info("Async report job %s complete: %s", job_id, report_path)
        _report_jobs[job_id] = rec
        _persist_job(job_id, rec)  # survive a worker recycle
    except Exception as e:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass
        logger.error("Async report job %s failed: %s", job_id, e)
        rec = {"status": "error", "error": str(e), "ts": time.time()}
        _report_jobs[job_id] = rec
        _persist_job(job_id, rec)


def _absolute_base_url(http_request: Request) -> str:
    """Public base URL (scheme://host) for building absolute poll links. Render
    terminates TLS at its proxy, so prefer the forwarded proto/host. Power
    Automate / Logic Apps only follows an ABSOLUTE Location header — every 202
    (the initial POST AND each running poll) must hand back an absolute URL, or
    the runtime stops polling after one cycle and returns the interim body."""
    proto = http_request.headers.get("x-forwarded-proto", http_request.url.scheme or "https")
    host = http_request.headers.get("x-forwarded-host") or http_request.headers.get("host")
    return f"{proto}://{host}" if host else str(http_request.base_url).rstrip("/")


@app.post("/generate-report-from-text-async")
async def generate_report_from_text_async(request: TranscriptRequest, http_request: Request):
    """Start report generation (incl. multi-minute web research) and return 202 + Location.

    Poll the Location URL until it returns the .docx (200). Enable Power
    Automate's "Asynchronous pattern" on the HTTP action to poll automatically.
    """
    if not request.transcript_text or not request.transcript_text.strip():
        raise HTTPException(status_code=400, detail="Transcript text is required and cannot be empty")
    flattened = flatten_jsonl_transcript(request.transcript_text)
    if not flattened or not flattened.strip():
        raise HTTPException(status_code=400, detail="Transcript text appears to be empty or invalid")
    meaningful_content = re.sub(r'[{}":\s\n\r]', '', flattened)
    if len(meaningful_content) < 50:
        raise HTTPException(status_code=400, detail="Transcript text appears to have insufficient content for report generation")

    _prune_report_jobs()
    job_id = uuid.uuid4().hex
    _report_jobs[job_id] = {"status": "running"}
    threading.Thread(
        target=_run_report_job,
        args=(job_id, flattened, request.address, request.last_name),
        daemon=True,
    ).start()
    logger.info("Started async report job %s (address=%r)", job_id, request.address)
    location = f"{_absolute_base_url(http_request)}/report-status/{job_id}"
    return JSONResponse(
        status_code=202,
        content={"job_id": job_id, "status": "running", "status_url": location},
        headers={"Location": location, "Retry-After": "20"},
    )


@app.get("/report-status/{job_id}")
async def report_status(job_id: str, http_request: Request):
    """Poll target for an async report: 202 while running, 200 with the .docx when done."""
    job = _report_jobs.get(job_id)
    if job is None:
        # In-memory miss — recover a COMPLETED job from its disk sidecar (survives
        # a worker recycle). A job that was still running when the worker died is
        # unrecoverable (its thread is gone), so it correctly stays a 404.
        job = _load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown or expired job id")
    if job["status"] == "running":
        # Absolute Location so the async-pattern poller keeps polling (a relative
        # next-poll URL here is why it stopped after one cycle / ~20s).
        location = f"{_absolute_base_url(http_request)}/report-status/{job_id}"
        return JSONResponse(
            status_code=202,
            content={"status": "running", "status_url": location},
            headers={"Location": location, "Retry-After": "20"},
        )
    if job["status"] == "error":
        raise HTTPException(status_code=500, detail=job.get("error", "Report generation failed"))
    if not job.get("path") or not os.path.exists(job["path"]):
        raise HTTPException(status_code=410, detail="Report file is no longer available")
    return FileResponse(
        path=job["path"],
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"PreWalkReport_{job.get('last_name') or 'Report'}.docx",
    )


@app.get("/config")
async def get_config(_: bool = Depends(require_admin)):
    """Get current configuration (admin only; secrets redacted)"""
    return _redact_config(config_manager.config)

@app.post("/config/reload")
async def reload_config(_: bool = Depends(require_admin)):
    """Reload configuration from file (admin only)"""
    config_manager.reload_config()
    return {"message": "Configuration reloaded", "config": _redact_config(config_manager.config)}

@app.put("/config/api-keys")
async def update_api_keys(
    anthropic_key: str = None,
    rapidapi_key: str = None,
    serpapi_key: str = None,
    _: bool = Depends(require_admin),
):
    """Update API keys dynamically (admin only).

    Note: the live pipeline reads keys from the environment / config.json at
    process start, so this only updates the on-disk config for the next reload.
    """
    config_manager.update_api_keys(anthropic_key, rapidapi_key, serpapi_key)
    return {"message": "API keys updated successfully"}

@app.put("/config/settings")
async def update_settings(
    max_file_size: int = None,
    timeout: int = None,
    enable_logging: bool = None,
    log_level: str = None,
    _: bool = Depends(require_admin),
):
    """Update server settings dynamically (admin only)"""
    if max_file_size is not None:
        config_manager.set("settings.max_file_size", max_file_size)
    if timeout is not None:
        config_manager.set("settings.timeout", timeout)
    if enable_logging is not None:
        config_manager.set("settings.enable_logging", enable_logging)
    if log_level is not None:
        config_manager.set("settings.log_level", log_level)
    return {"message": "Settings updated successfully"}

@app.put("/config/templates")
async def update_templates(
    default_template: str = None,
    _: bool = Depends(require_admin),
):
    """Update template settings (admin only)"""
    if default_template is not None:
        config_manager.set("templates.default_template", default_template)
    return {"message": "Template settings updated successfully"}

@app.post("/templates/upload")
async def upload_template(
    template_file: UploadFile = File(...),
    _: bool = Depends(require_admin),
):
    """Upload a new template file (admin only)"""
    try:
        # Reject anything but a .docx, and strip any path components from the
        # client-supplied filename to prevent path traversal (e.g. ../config.json).
        safe_name = os.path.basename(template_file.filename or "")
        if not safe_name or Path(safe_name).suffix.lower() not in ALLOWED_TEMPLATE_EXTS:
            raise HTTPException(status_code=415, detail="Only .docx templates are allowed.")

        template_dir = Path("templates")
        template_dir.mkdir(exist_ok=True)
        template_path = (template_dir / safe_name).resolve()
        if template_dir.resolve() != template_path.parent:
            raise HTTPException(status_code=400, detail="Invalid template path.")

        content = await template_file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Template file too large.")

        with open(template_path, "wb") as f:
            f.write(content)

        config_manager.set("templates.default_template", safe_name)
        return {"message": "Template uploaded successfully", "filename": safe_name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading template: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000
    ) 