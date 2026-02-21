#!/usr/bin/env python3
"""
Generate a sample report with neighboring projects
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "pre_walkthrough_generator" / "src"))

from neighboring_projects import NeighboringProjectsManager
from document_generator import DocumentGenerator

# Create sample data for 605 West 29th Street
sample_data = {
    "property_address": "605 West 29th Street, New York, NY 10001",
    "property_id": "1234567890",
    "realtor_url": "https://www.realtor.com/realestateandhomes-detail/605-W-29th-St_New-York_NY_10001",
    "property_details": {
        "address": "605 West 29th Street",
        "city": "New York",
        "state": "NY",
        "zip": "10001",
        "price": "$1,200,000",
        "bedrooms": "2",
        "bathrooms": "2",
        "sqft": "1,200",
        "year_built": "2010",
        "property_type": "Condo",
        "neighborhood": "Chelsea",
        "hoa_fee": "$800/month"
    },
    "images": {"images": []},
    "floor_plans": {"floor_plans": []},
    "transcript_info": {
        "property_address": "605 West 29th Street",
        "property_info": {
            "building_type": "Condo",
            "total_units": 50,
            "year_built": 2010,
            "building_rules": [
                "Submit renovation plans to board",
                "Contractor insurance required",
                "Work hours: 9 AM - 5 PM weekdays only"
            ],
            "building_features": ["Doorman", "Gym", "Roof deck"]
        },
        "client_info": {
            "names": ["John Smith", "Jane Smith"],
            "phone": "212-555-1234",
            "profession": "Finance professionals",
            "preferences": {
                "budget_sensitivity": "medium",
                "decision_making": "moderate",
                "design_involvement": "high",
                "quality_preference": "luxury"
            },
            "constraints": ["Must complete before summer", "Budget conscious"],
            "red_flags": {
                "is_negative_reviewer": False,
                "payment_concerns": False,
                "unrealistic_expectations": False,
                "communication_issues": False
            }
        },
        "renovation_scope": {
            "kitchen": {
                "description": "Complete kitchen gut renovation with high-end finishes",
                "estimated_cost": {"range": {"min": 80000, "max": 120000}},
                "plumbing_changes": "Relocate sink and dishwasher",
                "electrical_changes": "New panel, under-cabinet lighting, smart home integration",
                "specific_requirements": ["Custom Italian cabinetry", "Marble countertops"],
                "appliances": ["Sub-Zero refrigerator", "Wolf range", "Miele dishwasher"],
                "cabinets_and_countertops": {
                    "type": "Custom Italian cabinets",
                    "preferences": ["Calacatta marble", "Soft-close drawers"]
                }
            },
            "bathrooms": {
                "count": 2,
                "cost_per_bathroom": 35000,
                "plumbing_changes": "Full renovation both bathrooms",
                "specific_requirements": ["Heated floors", "Rain showerheads"],
                "fixtures": ["Toto toilets", "Kohler fixtures", "Custom vanities"],
                "finishes": ["Marble tile", "Glass shower enclosures"]
            },
            "additional_work": {
                "rooms": ["Living room", "Master bedroom", "Home office"],
                "structural_changes": ["Remove wall between kitchen and living room"],
                "systems_updates": ["New HVAC", "Smart home system"],
                "custom_features": ["Built-in bookshelves", "Custom closets"],
                "estimated_costs": {
                    "per_sqft_cost": 150,
                    "total_estimated_range": {"min": 200000, "max": 280000}
                }
            },
            "timeline": {
                "total_duration": "4-5 months",
                "phasing": "Kitchen and bathrooms first, then living spaces",
                "living_arrangements": "Clients will relocate during renovation",
                "constraints": ["Must complete by June 1st", "Minimize noise for neighbors"],
                "key_dates": {
                    "survey_completion": "March 15, 2026",
                    "walkthrough_scheduled": "March 1, 2026",
                    "project_start": "April 1, 2026"
                }
            }
        },
        "materials_and_design": {
            "sourcing_responsibility": "Chapter will source all materials with client approval",
            "specific_materials": ["Calacatta marble", "White oak flooring", "Brass fixtures"],
            "style_preferences": ["Modern", "Minimalist", "Scandinavian"],
            "quality_preferences": ["High-end", "Designer brands"]
        },
        "project_management": {
            "client_involvement": "High - weekly meetings",
            "design_services": ["3D renderings", "Material selection", "Color consultation"],
            "documentation_needs": ["Weekly progress photos", "Budget tracking"],
            "permit_requirements": ["DOB permits", "Landmark approval"],
            "company_details": {
                "company_name": "Chapter",
                "contact_person": "Massimo Pizzulli",
                "services_offered": ["Design", "Construction", "Project Management"],
                "fees_structure": ["10% deposit", "Progress payments"]
            }
        }
    },
    "neighboring_projects": []
}

print("Generating sample report with neighboring projects...")
print("=" * 60)

# Get neighboring projects
manager = NeighboringProjectsManager()
projects = manager.find_neighboring_projects(
    target_address="605 West 29th Street, New York, NY",
    target_neighborhood="Chelsea",
    same_building_only=False
)

print(f"Found {len(projects)} neighboring projects")
for proj in projects:
    print(f"  - {proj['deal_name']} (${proj['amount']:,}) - {proj['stage']}")

sample_data["neighboring_projects"] = projects

# Generate document
doc_gen = DocumentGenerator()
output_path = doc_gen.generate_report(
    sample_data,
    output_dir="data",
    file_name="Sample_Report_With_Neighboring_Projects.docx"
)

print("=" * 60)
print(f"✅ Report generated: {output_path}")
print("\n📄 Open the file to see:")
print("   1. Complete pre-walkthrough report")
print("   2. Neighboring Projects section with table")
print("   3. Projects organized by same building and neighborhood")
print("=" * 60)
