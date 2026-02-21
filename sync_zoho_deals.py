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
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sync_deals():
    """Fetch all deals from Zoho CRM and save to cache"""
    
    # Zoho credentials (should be in environment variables in production)
    client_id = os.getenv("ZOHO_CLIENT_ID", "1000.BTVCVLRAA929UPUKPQ4A0Y2XS3WK8M")
    client_secret = os.getenv("ZOHO_CLIENT_SECRET", "4f9ff22d9bcb4b68bb60af7fefc05616974e355296")
    refresh_token = os.getenv("ZOHO_REFRESH_TOKEN", "1000.3ff810c474ffec8f0521d0d86923c052.2d1d1c684c2e23ffbe9f8b024535cfee")
    
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
