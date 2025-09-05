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
            info_prompt = """Extract comprehensive structured information from this renovation consultation transcript. Pay special attention to budget numbers, timelines, specific project requirements, and client constraints.

Return ONLY valid JSON matching this exact structure:
{
    "property_address": string,  // The complete property address being renovated (extract exactly as mentioned)
    "property_info": {
        "building_type": string,  // e.g., "house", "condo", "co-op", "townhouse"
        "total_units": number or null,
        "year_built": number or null,
        "building_rules": string[],  // Any building/co-op rules mentioned
        "building_features": string[],  // Building amenities, features
        "realtor_property_id": string or null
    },
    "client_info": {
        "names": string[],  // All client names mentioned
        "phone": string,  // Phone number if mentioned
        "profession": string,  // Client's job/profession if mentioned
        "preferences": {
            "budget_sensitivity": string,  // How price-conscious they seem
            "decision_making": string,  // How they make decisions
            "design_involvement": string,  // How involved they want to be in design
            "quality_preference": string  // Their quality expectations
        },
        "constraints": string[],  // Any limitations or constraints mentioned (expecting child, timeline, etc.)
        "red_flags": {
            "is_negative_reviewer": boolean,  // Do they seem like they might leave bad reviews?
            "payment_concerns": boolean,  // Any concerns about their ability to pay?
            "unrealistic_expectations": boolean,  // Do they have unrealistic expectations?
            "communication_issues": boolean  // Any communication red flags?
        }
    },
    "renovation_scope": {
        "kitchen": {
            "description": string,  // Brief description of kitchen work needed
            "estimated_cost": {
                "range": {
                    "min": number,  // Minimum budget mentioned (extract actual numbers)
                    "max": number or null  // Maximum budget if range given
                }
            },
            "plumbing_changes": string,  // Any plumbing work mentioned
            "electrical_changes": string,  // Any electrical work mentioned
            "specific_requirements": string[],  // Specific things they want
            "appliances": string[],  // Appliances mentioned
            "cabinets_and_countertops": {
                "type": string,  // Type of cabinets/counters wanted
                "preferences": string[]  // Specific preferences
            },
            "constraints": string[]  // Any limitations or constraints
        },
        "bathrooms": {
            "count": number or null,  // How many bathrooms to renovate (extract as number, e.g., 2.5)
            "cost_per_bathroom": number or null,  // Budget per bathroom if mentioned
            "plumbing_changes": string,  // Plumbing work needed
            "specific_requirements": string[],  // Specific bathroom requirements (ensuite, etc.)
            "fixtures": string[],  // Fixtures mentioned (toilet, sink, etc.)
            "finishes": string[],  // Finishes mentioned (tile, etc.)
            "constraints": string[]  // Any bathroom constraints
        },
        "additional_work": {
            "rooms": string[],  // Specific rooms to add/modify (extract exact descriptions)
            "structural_changes": string[],  // Foundation, structural work mentioned
            "systems_updates": string[],  // HVAC, electrical, plumbing systems
            "custom_features": string[],  // Any custom features requested
            "estimated_costs": {
                "per_sqft_cost": number or null,  // Cost per square foot mentioned
                "total_estimated_range": {
                    "min": number or null,  // Minimum total project cost
                    "max": number or null   // Maximum total project cost
                },
                "architect_fees": {
                    "percentage": number or null,  // Architect fee percentage
                    "estimated_amount": number or null  // Estimated architect fee amount
                },
                "additional_fees": string[]  // Any other fees mentioned
            }
        },
        "timeline": {
            "total_duration": string,  // Expected project duration
            "phasing": string,  // How project will be phased
            "living_arrangements": string,  // Where client will live during renovation
            "constraints": string[],  // Timeline constraints (baby due, etc.)
            "key_dates": {
                "survey_completion": string,  // When survey results expected
                "walkthrough_scheduled": string,  // When walkthrough is planned
                "project_start": string  // When project might start
            }
        }
    },
    "materials_and_design": {
        "sourcing_responsibility": string,  // Who handles material sourcing
        "specific_materials": string[],  // Specific materials mentioned
        "style_preferences": string[],  // Design style preferences
        "quality_preferences": string[],  // Quality level preferences
        "trade_discounts": string[],  // Any trade discounts mentioned
        "reuse_materials": string[]  // Materials to reuse
    },
    "project_management": {
        "client_involvement": string,  // How involved client wants to be
        "design_services": string[],  // Design services needed
        "documentation_needs": string[],  // Permits, drawings needed
        "permit_requirements": string[],  // Permit requirements mentioned
        "contractor_requirements": string[],  // What they want from contractor
        "communication_preferences": string,  // How they prefer to communicate
        "decision_process": string,  // How they make decisions
        "company_details": {
            "company_name": string,  // Contractor company name
            "contact_person": string,  // Main contact person
            "services_offered": string[],  // Services the company offers
            "fees_structure": string[],  // Fee structure mentioned
            "process_description": string  // How their process works
        }
    }
}

CRITICAL EXTRACTION RULES:
1. BUDGET NUMBERS: Extract ALL dollar amounts mentioned - cost per sq ft, total estimates, architect fees, deposits, etc.
2. TIMELINE DETAILS: Extract specific dates, durations, and scheduling constraints
3. PROJECT SCOPE: Be very specific about what rooms/work is requested
4. CLIENT CONSTRAINTS: Note pregnancy, living arrangements, timeline pressures
5. COMPANY INFO: Extract contractor company details, process, fees
6. EXACT QUOTES: For requirements, use exact client language when possible
7. NUMBERS: Convert written numbers to digits (e.g., "two hundred fifty thousand" = 250000)
8. ADDRESSES: Extract complete address exactly as stated, fix obvious typos

Process this transcript and return ONLY the JSON:"""

            print("\nExtracting renovation information...")
            info_response = self.client.chat.completions.create(
                model="gpt-4o",  # Use the latest and most capable model
                messages=[
                    {"role": "system", "content": "You are an expert renovation consultant assistant that extracts comprehensive, detailed information from consultation transcripts. You pay close attention to budget numbers, timelines, specific requirements, and client constraints."},
                    {"role": "user", "content": info_prompt},
                    {"role": "user", "content": cleaned_transcript}
                ],
                temperature=0,
                max_tokens=4000,  # Increase token limit for more detailed extraction
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
        Extract the complete property address mentioned in this renovation consultation transcript.
        
        Look for the property address that the client wants renovated. This will typically be mentioned early in the conversation.
        
        Rules:
        • Return the EXACT address as mentioned, preserving the original format
        • Include apartment/unit numbers if mentioned (e.g., "#M7", "Apt 3B", "Unit 5")
        • Include the full city, state, and ZIP code
        • Do NOT modify or "correct" street names unless there's an obvious typo
        • Do NOT change abbreviations unless they're clearly wrong
        
        Examples of good output:
        - "268 Babbitt Road #M7, Bedford, NY 10507"
        - "1001 Unquowa Road, Fairfield, CT 06824"
        - "123 Main Street, Apt 4B, Brooklyn, NY 11201"
        
        Output ONLY the address, nothing else. If no clear address is found, output "NONE".
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use the latest model
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts addresses from text and corrects spelling mistakes in street names using context and common street names."},
                    {"role": "user", "content": prompt},
                    {"role": "user", "content": transcript}
                ],
                temperature=0,
                max_tokens=150
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
                model="gpt-4o",  # Use the latest model
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes client behavior and preferences."},
                    {"role": "user", "content": prompt},
                    {"role": "user", "content": transcript}
                ],
                temperature=0,
                max_tokens=1500
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
