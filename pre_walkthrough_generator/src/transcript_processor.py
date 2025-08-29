from openai import OpenAI
import json
from typing import Dict, Any, Optional
import re

class TranscriptProcessor:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def clean_transcript(self, transcript: str) -> str:
        """Clean the transcript by removing timestamps and formatting"""
        # Split into lines and clean
        lines = transcript.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Remove JSON formatting artifacts
            line = line.replace('{"":"', '').replace('"}', '')
            
            # Extract the actual message
            parts = line.split('|', 1)
            if len(parts) > 1:
                # Remove timestamp
                line = parts[0].strip()
            
            # Remove phone number format
            line = re.sub(r'\(\d{3}\)\s*\d{3}-\d{4}', '', line)
            # Remove +1 phone format
            line = re.sub(r'\+1\d{10}', '', line)
            
            # Clean up the line
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def extract_info(self, transcript: str) -> Dict[str, Any]:
        """Extract structured information from transcript"""
        # Clean the transcript first
        cleaned_transcript = transcript.strip()
        
        try:
            # Directly extract renovation and client information (no property ID)
            info_prompt = """Extract structured information from this renovation consultation transcript.

Return ONLY valid JSON matching this exact structure (property_id can be null):
{
    "property_info": {
        "building_type": string,
        "total_units": number or null,
        "year_built": number or null,
        "building_rules": string[],
        "building_features": string[],
        "realtor_property_id": string or null  // Use the provided property ID or null
    },
    "client_info": {
        "names": string[],
        "phone": string,
        "profession": string,
        "preferences": {
            "budget_sensitivity": string,
            "decision_making": string,
            "design_involvement": string,
            "quality_preference": string
        },
        "constraints": string[],
        "red_flags": {
            "is_negative_reviewer": boolean,
            "payment_concerns": boolean,
            "unrealistic_expectations": boolean,
            "communication_issues": boolean
        }
    },
    "renovation_scope": {
        "kitchen": {
            "description": string,
            "estimated_cost": {
                "range": {
                    "min": number,
                    "max": number or null
                }
            },
            "plumbing_changes": string,
            "electrical_changes": string,
            "specific_requirements": string[],
            "appliances": string[],
            "cabinets_and_countertops": {
                "type": string,
                "preferences": string[]
            },
            "constraints": string[]
        },
        "bathrooms": {
            "count": number or null,
            "cost_per_bathroom": number or null,
            "plumbing_changes": string,
            "specific_requirements": string[],
            "fixtures": string[],
            "finishes": string[],
            "constraints": string[]
        },
        "additional_work": {
            "rooms": string[],
            "structural_changes": string[],
            "systems_updates": string[],
            "custom_features": string[],
            "estimated_costs": object
        },
        "timeline": {
            "total_duration": string,
            "phasing": string,
            "living_arrangements": string,
            "constraints": string[]
        }
    },
    "materials_and_design": {
        "sourcing_responsibility": string,
        "specific_materials": string[],
        "style_preferences": string[],
        "quality_preferences": string[],
        "trade_discounts": string[],
        "reuse_materials": string[]
    },
    "project_management": {
        "client_involvement": string,
        "design_services": string[],
        "documentation_needs": string[],
        "permit_requirements": string[],
        "contractor_requirements": string[],
        "communication_preferences": string,
        "decision_process": string
    }
}

Process this transcript and return the JSON:"""

            print("\nExtracting renovation information...")
            info_response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured information from renovation consultation transcripts."},
                    {"role": "user", "content": info_prompt},
                    {"role": "user", "content": cleaned_transcript}
                ],
                temperature=0,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Get the response content
            response_text = info_response.choices[0].message.content
            print("\nAPI Response:")
            print(response_text)
            
            # Extract the JSON response and convert to template
            data = json.loads(response_text)
            
            return data
            
        except Exception as e:
            print(f"\nError extracting information: {e}")
            return {}

    def extract_address(self, transcript: str) -> str:
        prompt = """
        Extract the single most likely full street address mentioned in this transcript.
        Only output addresses located in: New York (all boroughs), New Jersey, Westchester County NY, Connecticut, or Miami-Dade FL.

        Normalise rules:
        • Expand abbreviations: Pl→Place, St→Street, Ave→Avenue, Rd→Road, Ct→Court, Pkwy→Parkway.
        • Convert spelled-out numbers to digits.
        • Convert Apartment/Apt/Unit variations to "Apt N".
        • Include 5-digit ZIP.
        • If you detect a likely spelling mistake in the street name (e.g. "Pierpont" instead of "Pierrepont"), correct it using context and common NYC/Brooklyn street names. Use fuzzy matching and context to infer the correct spelling if possible.
        • If the transcript contains a street name that is a close match to a well-known street in the area, correct the spelling to the canonical name.

        Output exactly: "number Street Name[, Apt X], City, State ZIP" – one line, no extra text.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts addresses from text and corrects spelling mistakes in street names using context and common NYC/Brooklyn street names."},
                    {"role": "user", "content": prompt},
                    {"role": "user", "content": transcript}
                ],
                temperature=0,
                max_tokens=100
            )
            addr = response.choices[0].message.content.strip()
            if addr and addr.lower() != 'none' and len(addr) > 8:
                return addr
        except Exception:
            pass

        # Fallback: regex for NYC-style addresses with fuzzy street name correction
        import re
        from difflib import get_close_matches
        # List of common Brooklyn/NYC street names for fuzzy correction
        common_streets = [
            "Pierrepont", "Montague", "Court", "Clinton", "Henry", "Hicks", "Willoughby", "Schermerhorn", "Atlantic", "Fulton", "Flatbush", "Dekalb", "Jay", "Smith", "Bond", "Hoyt", "Nevins", "Sackett", "Union", "Carroll", "President", "St Marks", "4th Avenue", "5th Avenue", "6th Avenue", "7th Avenue", "8th Avenue", "9th Street", "Prospect Park West", "Eastern Parkway", "Bedford", "Nostrand", "Marcy", "Tompkins", "Gates", "Greene", "Lafayette", "Putnam", "Jefferson", "Madison", "Lexington", "Park", "Lenox", "St Nicholas", "Broadway", "Metropolitan", "Grand", "Driggs", "Manhattan", "Graham", "Lorimer", "McGuinness", "Franklin", "Kent", "Wythe", "Berry", "Havemeyer", "Roebling", "Union Avenue", "Bushwick", "Knickerbocker", "Irving", "Wilson", "Central", "Myrtle", "DeKalb", "Hart", "Himrod", "Stanhope", "Grove", "Menahan", "Cornelia", "Jefferson", "Putnam", "Madison", "Monroe", "Gates", "Greene", "Lafayette", "Clifton", "Parkside", "Ocean", "Empire", "Sterling", "Lincoln", "Maple", "Rutland", "Winthrop", "Clark", "Pineapple", "Orange", "Cranberry", "Willow", "Columbia Heights", "Poplar", "State", "Joralemon", "Remsen", "Livingston", "Boerum", "Dean", "Bergen", "Pacific", "Warren", "Baltic", "Butler", "Douglass", "Wyckoff", "Bond", "Nevins", "3rd Avenue", "4th Avenue", "5th Avenue", "6th Avenue", "7th Avenue", "8th Avenue", "9th Avenue"
        ]
        lines = transcript.split('\n')
        for line in lines:
            m = re.search(r"(\d+\s*[NSEW]?[\s\d]*\w+\s*(?:st|street|ave|avenue|rd|road|blvd|drive|dr|pl|place)[^,\n]*)(?:,?\s*(apt|apartment|unit)\s*([\w\d]+))?", line, re.IGNORECASE)
            if m:
                street = m.group(1).strip()
                apt = m.group(3)
                # Fuzzy correct the street name
                street_parts = street.split()
                if len(street_parts) >= 2:
                    # Find the part that is likely the street name
                    for i in range(1, len(street_parts)):
                        candidate = street_parts[i].capitalize()
                        matches = get_close_matches(candidate, common_streets, n=1, cutoff=0.8)
                        if matches:
                            street_parts[i] = matches[0]
                            break
                    street = ' '.join(street_parts)
                # Try to infer city/borough
                city = "Brooklyn"
                state = "NY"
                zip_code = ""
                for borough in ["Brooklyn", "Manhattan", "Queens", "Bronx", "New York", "NYC"]:
                    if borough.lower() in line.lower():
                        city = borough
                        break
                zip_match = re.search(r"\b(1\d{4}|07\d{3}|10\d{3}|11\d{3}|100\d{2}|112\d{2}|104\d{2}|073\d{2}|331\d{2})\b", line)
                if zip_match:
                    zip_code = zip_match.group(1)
                addr = f"{street}"
                if apt:
                    addr += f", Apt {apt}"
                addr += f", {city}, {state}"
                if zip_code:
                    addr += f" {zip_code}"
                return addr
        return ""

    def analyze_client(self, transcript: str) -> Dict[str, Any]:
        """Analyze client behavior and preferences"""
        prompt = """
        Analyze the client's behavior, communication style, and potential red flags from this renovation consultation transcript.
        Focus on:
        1. Communication style
        2. Decision-making process
        3. Budget sensitivity
        4. Past renovation experiences
        5. Review history (especially negative reviews)
        6. Expectations vs reality
        7. Payment discussions
        8. Professional background
        9. Design preferences
        10. Project management style

        Return the analysis in this JSON format:
        {
            "client_profile": {
                "name": "",
                "profession": "",
                "communication_style": "direct/indirect/mixed",
                "decision_making": "quick/moderate/slow",
                "budget_sensitivity": "low/medium/high"
            },
            "risk_assessment": {
                "is_negative_reviewer": false,
                "payment_concerns": false,
                "unrealistic_expectations": false,
                "communication_issues": false,
                "evidence": []
            },
            "preferences": {
                "design_involvement": "low/medium/high",
                "quality_level": "basic/mid-range/luxury",
                "timeline_flexibility": "low/medium/high"
            },
            "background": {
                "renovation_experience": "none/some/extensive",
                "relevant_expertise": "",
                "notable_comments": []
            }
        }
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes client behavior and preferences."},
                    {"role": "user", "content": prompt},
                    {"role": "user", "content": transcript}
                ],
                temperature=0,
                max_tokens=1000
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error analyzing client: {e}")
            return {}

    def process_transcript_text(self, transcript: str) -> Dict[str, Any]:
        """High-level helper used by serverless handler.

        1. Clean raw transcript (remove timestamps, etc.)
        2. Extract structured information via GPT (extract_info)
        3. Ensure the template contains a property address – if missing, try address extraction.
        """
        # Step 1 – basic cleaning so the LLM prompt is smaller
        cleaned = self.clean_transcript(transcript)

        # Step 2 – get structured info
        info_data = self.extract_info(cleaned)

        # Step 3 – populate address if the LLM didn’t include it
        try:
            if not info_data.get("property_info") or not info_data["property_info"].get("address") or not info_data["property_info"]["address"].get("full"):
                addr = self.extract_address(cleaned)
                if addr:
                    # mutate info_data in-place so downstream code sees the address
                    info_data["property_info"]["address"]["full"] = addr  # type: ignore[attr-defined]
        except Exception:
            # Fail silently – downstream code will fall back to empty address handling
            pass

        return info_data
