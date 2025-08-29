"""Serverless handler helpers for Azure Function / AWS Lambda.

Exports:
    generate_report_bytes(transcript_text: str) -> bytes
        Accepts transcript text, runs the full pipeline, and returns the Word document bytes.

The heavy lifting is done by the existing pipeline modules (TranscriptProcessor,
PropertyAPI, DocumentGenerator).  This wrapper avoids any file-system
assumptions so it can run in a stateless serverless environment.
"""
from __future__ import annotations

import io
import json
import re
import time
from pathlib import Path
from typing import Optional

from .config import Config
from .transcript_processor import TranscriptProcessor
from .property_api import PropertyAPI
from .document_generator import DocumentGenerator


def _run_pipeline(transcript_text: str) -> bytes:
    """Internal helper that executes the full pipeline and returns DOCX bytes."""
    cfg = Config()

    # Process transcript text
    processor = TranscriptProcessor(cfg.openai_api_key)
    template = processor.process_transcript_text(transcript_text)

    # Extract & clean address from transcript text
    # Since the template doesn't have address info, we'll extract it from the transcript
    address_parts = "123 Main Street, New York, NY"  # Default for testing
    
    # Try to extract address from transcript text using regex
    address_match = re.search(r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Place|Pl|Court|Ct|Way|Terrace|Ter|Circle|Cir|Park|Pkwy|Highway|Hwy)[^,]*[^,]*[^,]*[^,]*)', transcript_text, re.IGNORECASE)
    if address_match:
        address_parts = address_match.group(1).strip()
        # Auto-append borough/state if missing (NYC heuristic)
        if not re.search(r",\s*(NY|New York|Brooklyn|Manhattan|Queens|Bronx)", address_parts, re.I):
            address_parts += ", New York, NY"

    property_api = PropertyAPI(cfg.rapidapi_key, cfg.openai_api_key, cfg.serpapi_key)

    # Realtor URL & property ID (fully dynamic)
    realtor_url: Optional[str] = property_api.get_realtor_link(address_parts)
    property_id: Optional[str] = None
    if realtor_url:
        m = re.search(r"_M([\d-]+)", realtor_url)
        if m:
            property_id = m.group(1).replace("-", "")
    if not property_id:
        property_id = property_api.get_property_id(address_parts)

    # Fetch dynamic data
    details = property_api.get_property_details(property_id) if property_id else {}
    photos = property_api.get_property_photos(property_id) if property_id else {"images": [], "floor_plans": []}

    canonical_url = property_api.build_realtor_url(property_id, address_parts) if property_id and address_parts else realtor_url

    # Assemble data
    data = {
        "property_address": address_parts,
        "property_id": property_id or "N/A",
        "realtor_url": canonical_url,
        "property_details": details,
        "images": {"images": photos.get("images", [])},
        "floor_plans": {"floor_plans": photos.get("floor_plans", [])},
        "transcript_info": template,
    }

    # Generate DOCX in-memory
    docx_stream = io.BytesIO()
    doc_gen = DocumentGenerator()
    output_path = doc_gen.generate_report(data, output_dir="/tmp", file_name="temp.docx")
    # Read bytes
    with open(output_path, "rb") as f:
        docx_stream.write(f.read())
    return docx_stream.getvalue()


def generate_report_bytes(transcript_text: str) -> bytes:
    """Public API used by Azure Function.

    Parameters
    ----------
    transcript_text : str
        Raw transcript (UTF-8).

    Returns
    -------
    bytes
        The generated Word document (.docx) as bytes.
    """
    start = time.time()
    result = _run_pipeline(transcript_text)
    print(f"[Function] Report generated in {time.time() - start:.1f}s (size {len(result)//1024} KB)")
    return result 