#!/usr/bin/env python3
"""
Sync Zoho CRM Deals to Local Cache
Run this script periodically (e.g., via cron) to keep the cache fresh
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "pre_walkthrough_generator" / "src"))

from zoho_api import ZohoAPI
from neighboring_projects import NeighboringProjectsManager
from nyc_neighborhoods import enrich_deals_with_neighborhoods
import logging

try:
    from config import get_config
except Exception:  # pragma: no cover
    get_config = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sync_deals():
    """Fetch all deals from Zoho CRM and save to cache"""
    
    # Zoho credentials from environment variables
    client_id = os.getenv("ZOHO_CLIENT_ID")
    client_secret = os.getenv("ZOHO_CLIENT_SECRET")
    refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")

    # Fall back to config.json if the environment doesn't carry the credentials.
    if not all([client_id, client_secret, refresh_token]) and get_config:
        cfg = get_config()
        client_id = client_id or cfg.zoho_client_id
        client_secret = client_secret or cfg.zoho_client_secret
        refresh_token = refresh_token or cfg.zoho_refresh_token

    if not all([client_id, client_secret, refresh_token]):
        logger.error("Missing Zoho credentials. Please set ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, and ZOHO_REFRESH_TOKEN environment variables.")
        return False
    
    try:
        # Initialize Zoho API
        logger.info("Initializing Zoho API...")
        zoho = ZohoAPI(client_id, client_secret, refresh_token)
        
        # Fetch all deals
        logger.info("Fetching deals from Zoho CRM...")
        fields = ["Deal_Name", "Amount", "Stage", "Contact_Name", "Closing_Date"]
        deals = zoho.get_all_records("Deals", fields=fields, max_records=5000)
        
        if not deals:
            logger.warning("No deals fetched from Zoho CRM")
            return False
        
        logger.info(f"Fetched {len(deals)} deals from Zoho CRM")

        # Tag each deal with its NYC neighborhood BEFORE caching — without this the
        # cache has no Neighborhood field and report-time matching always returns 0.
        logger.info("Enriching deals with neighborhoods...")
        enrich_deals_with_neighborhoods(deals, use_geocoding=True)

        # Save to cache
        logger.info("Saving deals to cache...")
        manager = NeighboringProjectsManager()
        manager.save_cache(deals)
        
        # Print cache stats
        stats = manager.get_cache_stats()
        logger.info(f"Cache stats: {stats}")
        
        logger.info("✅ Sync completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error syncing deals: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = sync_deals()
    sys.exit(0 if success else 1)
