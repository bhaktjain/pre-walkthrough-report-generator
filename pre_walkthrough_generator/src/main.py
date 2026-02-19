import os
import sys
from pathlib import Path
import re
import json
from .config import Config
from .transcript_processor import TranscriptProcessor
from .property_api import PropertyAPI
from .document_generator import DocumentGenerator

def clean_transcript(raw_transcript: str) -> str:
    """Clean the transcript text"""
    # Remove any special characters or formatting
    transcript = raw_transcript.strip()
    return transcript

def clean_address(address: str) -> str:
    """Clean and standardize address format"""
    # Remove extra whitespace
    address = ' '.join(address.split())
    # Convert apartment/unit variations to standard format
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

def save_json(data: dict, filename: str):
    """Save data to JSON file"""
    output_path = Path("data") / filename
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(filename: str) -> dict:
    """Load data from JSON file"""
    try:
        input_path = Path("data") / filename
        with open(input_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return {}

def main():
    # Initialize components
    config = Config()
    doc_generator = DocumentGenerator()
    transcript_processor = TranscriptProcessor(config.openai_api_key)
    property_api = PropertyAPI(config.rapidapi_key, config.openai_api_key, config.serpapi_key)

    def resolve_transcript_paths(args) -> list[Path]:
        """Return a list of transcript Path objects to process based on CLI args."""
        transcripts_dir = Path("data/transcripts")

        # 1. If user passes 'all', process every *.txt in the directory
        if args and args[0].lower() == 'all':
            return sorted(transcripts_dir.glob("*.txt"), key=lambda p: p.stat().st_mtime)

        # 2. If specific filenames are provided, try to locate them
        if args:
            paths = []
            for arg in args:
                p = Path(arg)
                if not p.exists():
                    p = transcripts_dir / arg  # fall back to transcripts directory
                if p.exists() and p.suffix.lower() == '.txt':
                    paths.append(p.resolve())
                else:
                    print(f"Warning: transcript not found or invalid extension -> {arg}")
            return paths

        # 3. Default: process newest transcript only (original behaviour)
        txt_files = list(transcripts_dir.glob("*.txt"))
        if not txt_files:
            return []
        newest = max(txt_files, key=lambda p: p.stat().st_mtime)
        return [newest]

    transcripts_to_process = resolve_transcript_paths(sys.argv[1:])

    if not transcripts_to_process:
        print("No transcript files found to process.")
        sys.exit(1)

    try:
        for transcript_path in transcripts_to_process:
            if not transcript_path.exists():
                print(f"\nError: Transcript file not found: {transcript_path}")
                continue

            print(f"\n==============================\nProcessing transcript: {transcript_path.name}")
            with open(transcript_path, 'r') as f:
                transcript = clean_transcript(f.read())
            transcript_info = transcript_processor.extract_info(transcript)

            # save individual json per transcript
            save_json(transcript_info, f"transcript_info_{transcript_path.stem}.json")
            print("Transcript processed and saved.")

            # Dynamically extract address from transcript
            address = transcript_processor.extract_address(transcript)
            if not address:
                # Try to match any plausible address substring (maximally permissive)
                fname = transcript_path.stem.replace('_', ' ').replace('-', ' ')
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
                else:
                    # Final fallback: always use the filename as address, append Brooklyn, NY
                    address = fname + ", Brooklyn, NY"
            if address:
                address = clean_address(address)
                # Only add Brooklyn, NY if the address doesn't already have a city, state
                # Check if address already has a proper city, state format
                if not re.search(r",\s*[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}", address):
                    # Only add if it looks like a street address without city/state
                    if re.match(r"\d+\s*[NSEW]?\s*\d*\s*\w+\s*(st|street|ave|avenue|rd|road|blvd|drive|dr|pl|place)", address, re.IGNORECASE):
                        if not re.search(r",\s*(brooklyn|manhattan|queens|bronx|new york|ny|nyc|nj|jersey|miami|fl|florida|ct|connecticut|westchester)", address, re.IGNORECASE):
                            address += ", Brooklyn, NY"
            else:
                address = ""

            # Remove static fallback for Pierrepont
            # Only use dynamic extraction and API lookups

            # Retrieve Realtor.com link and property ID
            realtor_url = property_api.get_realtor_link(address)
            property_id = None
            if realtor_url:
                property_id_match = re.search(r'_M([\d-]+)', realtor_url)
                property_id = property_id_match.group(1).replace('-', '') if property_id_match else None
            if not property_id:
                # Fallback: use get_property_id (OpenAI + web scrape)
                property_id = property_api.get_property_id(address)

            # Always fetch property details from /v2/property
            property_details = property_api.get_property_details(property_id) if property_id else {}
            print("\n[DEBUG] property_details returned from property_api:")
            print(json.dumps(property_details, indent=2, default=str))

            # Always fetch images and floor plans from /propertyPhotos
            property_photos = property_api.get_property_photos(property_id) if property_id else {"images": [], "floor_plans": []}
            print("\n[DEBUG] property_photos returned from property_api:")
            print(json.dumps(property_photos, indent=2, default=str))

            # Always use canonical Realtor.com URL if possible
            canonical_realtor_url = property_api.build_realtor_url(property_id, address) if property_id and address else realtor_url

            # Create final data dictionary
            final_data = {
                "property_address": address,
                "property_id": property_id or "N/A",
                "realtor_url": canonical_realtor_url,
                "property_details": property_details,
                "images": {"images": property_photos.get('images', [])},
                "floor_plans": {"floor_plans": property_photos.get('floor_plans', [])},
                "transcript_info": transcript_info
            }

            print("\n[DEBUG] property_details passed to DocumentGenerator:")
            print(json.dumps(property_details, indent=2, default=str))
            print("\n[DEBUG] property_photos passed to DocumentGenerator:")
            print(json.dumps(property_photos, indent=2, default=str))
            print(f"[DEBUG] Canonical Realtor.com URL: {canonical_realtor_url}")

            save_json(final_data, f"final_data_{transcript_path.stem}.json")

            # Generate report
            print("\nGenerating pre-walkthrough report...")
            
            # Sanitize address for filename
            if address:
                safe_addr = address.split(',')[0]
                # Remove invalid filename characters
                invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '#']
                for char in invalid_chars:
                    safe_addr = safe_addr.replace(char, '_')
                safe_addr = safe_addr.replace(' ', '_')
                # Replace multiple underscores with single
                while '__' in safe_addr:
                    safe_addr = safe_addr.replace('__', '_')
                safe_addr = safe_addr.strip('_')
            else:
                safe_addr = transcript_path.stem
            
            output_path = doc_generator.generate_report(final_data, file_name=f"PreWalk_{safe_addr}.docx")
            if not output_path:
                print("\nError generating report")
                continue

            print(f"Report generated successfully at: {output_path}")

            # Console summary (optional)
            print("\nSummary:")
            print(f"Address: {address}")
            print(f"Realtor URL: {canonical_realtor_url or 'N/A'}")
            if property_id:
                print(f"Property ID: M{property_id}")
            print("All data saved to data directory.")

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
