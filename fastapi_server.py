from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import uvicorn
import tempfile
import os
import sys
from pathlib import Path
import logging
import json
import re
from config_manager import config_manager
import time
from datetime import datetime
from pydantic import BaseModel

# Add the pre_walkthrough_generator to the path
sys.path.append(str(Path(__file__).parent / "pre_walkthrough_generator" / "src"))

# Import the modules directly to avoid relative import issues
try:
    import config
    import transcript_processor
    import property_api
    import document_generator
    from neighboring_projects import NeighboringProjectsManager
except ImportError as e:
    logging.error(f"Import error: {e}")
    raise
except Exception as e:
    logging.error(f"Configuration error: {e}")
    # Continue anyway - the config will be handled by environment variables
    import transcript_processor
    import property_api
    import document_generator
    from neighboring_projects import NeighboringProjectsManager

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

@app.on_event("startup")
async def startup_sync_zoho_cache():
    """On startup, try to refresh Zoho deals cache if stale and credentials are available."""
    try:
        manager = NeighboringProjectsManager()
        stats = manager.get_cache_stats()
        logger.info(f"Zoho cache stats on startup: {stats}")
        
        if stats.get('valid') and stats.get('count', 0) > 0:
            logger.info(f"Zoho cache is valid ({stats['count']} deals, {stats.get('age_hours', 0):.1f}h old). Skipping sync.")
            return
        
        # Cache is missing or stale — try to sync
        zoho_client_id = os.environ.get("ZOHO_CLIENT_ID")
        zoho_client_secret = os.environ.get("ZOHO_CLIENT_SECRET")
        zoho_refresh_token = os.environ.get("ZOHO_REFRESH_TOKEN")
        
        if not all([zoho_client_id, zoho_client_secret, zoho_refresh_token]):
            logger.warning("Zoho credentials not configured. Neighboring projects will use existing cache if available.")
            return
        
        logger.info("Zoho cache is stale or missing. Syncing deals...")
        from zoho_api import ZohoAPI
        zoho = ZohoAPI(zoho_client_id, zoho_client_secret, zoho_refresh_token)
        fields = ["Deal_Name", "Amount", "Stage", "Contact_Name", "Closing_Date"]
        deals = zoho.get_all_records("Deals", fields=fields, max_records=5000)
        
        if deals:
            manager.save_cache(deals)
            logger.info(f"Zoho cache refreshed: {len(deals)} deals")
        else:
            logger.warning("No deals returned from Zoho API")
    except Exception as e:
        logger.error(f"Startup Zoho sync failed (non-fatal): {e}")


@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    uptime = datetime.now() - server_metrics["start_time"]
    return {
        "status": "healthy",
        "uptime_seconds": uptime.total_seconds(),
        "requests_processed": server_metrics["requests_processed"],
        "errors": server_metrics["errors"],
        "last_request": server_metrics["last_request"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics")
async def get_metrics():
    """Get detailed server metrics"""
    return {
        "server_metrics": server_metrics,
        "config": config_manager.config,
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

def process_transcript_and_generate_report(transcript_path: str, address: str = None, last_name: str = None) -> str:
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
        transcript_processor_obj = transcript_processor.TranscriptProcessor(config_obj.openai_api_key)
        property_api_obj = property_api.PropertyAPI(config_obj.rapidapi_key, config_obj.openai_api_key, config_obj.serpapi_key)

        # Read and clean transcript
        with open(transcript_path, 'r') as f:
            transcript = clean_transcript(f.read())
        
        logger.info(f"Processing transcript: {transcript_path}")
        
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

        # Use the optimized method to get all property data in one go
        logger.info("Fetching all property data...")
        property_data = property_api_obj.get_all_property_data(address)
        
        # Extract the components
        property_id = property_data.get("property_id", "N/A")
        property_details = property_data.get("property_details", {})
        property_photos = property_data.get("images", {"images": []})
        floor_plans = property_data.get("floor_plans", {"floor_plans": []})
        canonical_realtor_url = property_data.get("realtor_url")
        
        logger.info(f"Property ID: {property_id}")
        logger.info(f"Realtor URL: {canonical_realtor_url}")
        
        # Check if property details are missing (validation failed)
        if not property_details or not property_details.get('address'):
            logger.warning("⚠️  Property details are missing or validation failed!")
            logger.warning(f"⚠️  Requested address: {address}")
            logger.warning("⚠️  This could mean:")
            logger.warning("   1. Property not found on Realtor.com")
            logger.warning("   2. Property ID lookup returned wrong property (validation rejected it)")
            logger.warning("   3. Property is off-market or recently delisted")
            logger.warning("⚠️  Report will be generated with limited property information")
        
        # Fetch neighboring projects from Zoho CRM cache
        logger.info("Looking up neighboring projects...")
        neighboring_projects = []
        try:
            projects_manager = NeighboringProjectsManager()
            
            # Extract neighborhood from property details if available
            neighborhood = None
            if property_details and isinstance(property_details, dict):
                neighborhood = property_details.get('neighborhood', None)
                if neighborhood == 'Information not available':
                    neighborhood = None
            
            # Always try to find neighboring projects using address-based neighborhood lookup
            logger.info(f"Searching for neighboring projects (neighborhood from API: {neighborhood})")
            neighboring_projects = projects_manager.find_neighboring_projects(
                target_address=address,
                target_neighborhood=neighborhood,
                same_building_only=False
            )
            logger.info(f"Found {len(neighboring_projects)} neighboring projects")
        except Exception as e:
            logger.error(f"Error fetching neighboring projects: {e}")
            import traceback
            traceback.print_exc()
            # Continue without neighboring projects

        # Create final data dictionary
        final_data = {
            "property_address": address,
            "property_id": property_id,
            "realtor_url": canonical_realtor_url,
            "property_details": property_details,
            "images": property_photos,
            "floor_plans": floor_plans,
            "transcript_info": transcript_info,
            "neighboring_projects": neighboring_projects
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
        
        if last_name:
            safe_last_name = sanitize_filename(last_name)
            file_name = f"PreWalk_{safe_last_name}.docx"
        else:
            file_name = f"PreWalk_{safe_addr}.docx"
        
        output_path = doc_generator.generate_report(final_data, file_name=file_name)
        
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
        
        # Create a temporary file to save the uploaded transcript
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{transcript_file.filename}") as temp_file:
            content = await transcript_file.read()
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
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@app.get("/config")
async def get_config():
    """Get current configuration"""
    return config_manager.config

@app.post("/config/reload")
async def reload_config():
    """Reload configuration from file"""
    config = config_manager.reload_config()
    return {"message": "Configuration reloaded", "config": config}

@app.put("/config/api-keys")
async def update_api_keys(
    openai_key: str = None,
    rapidapi_key: str = None,
    serpapi_key: str = None
):
    """Update API keys dynamically"""
    config_manager.update_api_keys(openai_key, rapidapi_key, serpapi_key)
    return {"message": "API keys updated successfully"}

@app.put("/config/settings")
async def update_settings(
    max_file_size: int = None,
    timeout: int = None,
    enable_logging: bool = None,
    log_level: str = None
):
    """Update server settings dynamically"""
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
    default_template: str = None
):
    """Update template settings"""
    if default_template is not None:
        config_manager.set("templates.default_template", default_template)
    return {"message": "Template settings updated successfully"}

@app.post("/templates/upload")
async def upload_template(
    template_file: UploadFile = File(...)
):
    """Upload a new template file"""
    try:
        # Save template to templates directory
        template_dir = Path("templates")
        template_dir.mkdir(exist_ok=True)
        
        template_path = template_dir / template_file.filename
        with open(template_path, "wb") as f:
            content = await template_file.read()
            f.write(content)
        
        # Update config to use new template
        config_manager.set("templates.default_template", template_file.filename)
        
        return {
            "message": "Template uploaded successfully",
            "filename": template_file.filename,
            "path": str(template_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading template: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000
    ) 