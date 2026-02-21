"""
Enhance Zoho deals cache with neighborhood information
Looks up each deal address and adds neighborhood data
"""
import sys
from pathlib import Path
import json
import os
import time
from datetime import datetime

sys.path.append(str(Path(__file__).parent / "pre_walkthrough_generator" / "src"))

from dotenv import load_dotenv
load_dotenv()

from property_api import PropertyAPI

def enhance_cache_with_neighborhoods():
    """Add neighborhood information to each deal in the cache"""
    
    # Load environment variables
    serpapi_key = os.getenv('SERPAPI_KEY')
    rapidapi_key = os.getenv('RAPIDAPI_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not rapidapi_key:
        print("ERROR: RAPIDAPI_KEY not found in environment")
        return
    
    # Initialize PropertyAPI
    api = PropertyAPI(rapidapi_key, openai_key, serpapi_key)
    
    # Load cache
    cache_file = Path("data/cache/zoho_deals_cache.json")
    if not cache_file.exists():
        print("ERROR: Cache file not found")
        return
    
    with open(cache_file, 'r') as f:
        cache_data = json.load(f)
    
    deals = cache_data.get('deals', [])
    print(f"Loaded {len(deals)} deals from cache")
    print()
    
    # Track progress
    enhanced_count = 0
    failed_count = 0
    skipped_count = 0
    
    # Process each deal
    for i, deal in enumerate(deals, 1):
        deal_name = deal.get('Deal_Name', '')
        
        # Skip if already has neighborhood
        if 'Neighborhood' in deal and deal['Neighborhood']:
            skipped_count += 1
            if i % 100 == 0:
                print(f"Progress: {i}/{len(deals)} - {enhanced_count} enhanced, {skipped_count} skipped, {failed_count} failed")
            continue
        
        # Use deal name as address
        address = deal_name
        
        if not address:
            skipped_count += 1
            continue
        
        try:
            # Get property ID
            property_id = api.get_property_id(address)
            
            if property_id:
                # Get property details
                time.sleep(0.5)  # Rate limiting
                details = api.get_property_details(property_id)
                
                if details and details.get('neighborhood'):
                    neighborhood = details['neighborhood']
                    deal['Neighborhood'] = neighborhood
                    enhanced_count += 1
                    print(f"{i}. {deal_name}")
                    print(f"   → {neighborhood}")
                else:
                    deal['Neighborhood'] = None
                    failed_count += 1
            else:
                deal['Neighborhood'] = None
                failed_count += 1
        
        except Exception as e:
            print(f"ERROR processing {deal_name}: {e}")
            deal['Neighborhood'] = None
            failed_count += 1
        
        # Progress update every 10 deals
        if i % 10 == 0:
            print(f"Progress: {i}/{len(deals)} - {enhanced_count} enhanced, {skipped_count} skipped, {failed_count} failed")
            
            # Save intermediate progress
            cache_data['deals'] = deals
            cache_data['last_enhanced'] = datetime.now().isoformat()
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
    
    # Final save
    cache_data['deals'] = deals
    cache_data['last_enhanced'] = datetime.now().isoformat()
    cache_data['enhanced_count'] = enhanced_count
    
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    print()
    print("="*80)
    print("ENHANCEMENT COMPLETE")
    print("="*80)
    print(f"Total deals: {len(deals)}")
    print(f"Enhanced: {enhanced_count}")
    print(f"Skipped (already had neighborhood): {skipped_count}")
    print(f"Failed: {failed_count}")
    print()
    print(f"Cache saved to: {cache_file}")

if __name__ == "__main__":
    print("="*80)
    print("ENHANCE CACHE WITH NEIGHBORHOODS")
    print("="*80)
    print()
    print("This will look up neighborhood information for each deal")
    print("and add it to the cache for better matching.")
    print()
    
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        enhance_cache_with_neighborhoods()
    else:
        print("Cancelled")
