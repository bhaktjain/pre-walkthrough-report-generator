#!/usr/bin/env python3
"""
Enrich all cached Zoho deals with neighborhood information.
Uses local ZIP mapping first, then Nominatim geocoding for unresolved addresses.
Results are cached so subsequent runs are fast.
"""

import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "pre_walkthrough_generator" / "src"))

from nyc_neighborhoods import (
    get_neighborhood_from_address,
    enrich_deals_with_neighborhoods,
    _load_geocode_cache,
    _save_geocode_cache,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CACHE_FILE = Path("data/cache/zoho_deals_cache.json")


def main():
    if not CACHE_FILE.exists():
        logger.error("No deals cache found. Run sync_zoho_deals.py first.")
        return

    with open(CACHE_FILE, 'r') as f:
        cache_data = json.load(f)

    deals = cache_data.get("deals", [])
    logger.info(f"Loaded {len(deals)} deals from cache")

    # First pass: local matching only (fast)
    local_matched = 0
    needs_geocoding = []
    for i, deal in enumerate(deals):
        name = deal.get("Deal_Name", "")
        hood = get_neighborhood_from_address(name, use_geocoding=False)
        if hood:
            deal["Neighborhood"] = hood
            local_matched += 1
        else:
            needs_geocoding.append(i)
            deal["Neighborhood"] = None

    logger.info(f"Local matching: {local_matched}/{len(deals)} matched")
    logger.info(f"Need geocoding: {len(needs_geocoding)} deals")

    # Second pass: geocode unmatched addresses
    geocoded = 0
    for count, idx in enumerate(needs_geocoding):
        deal = deals[idx]
        name = deal.get("Deal_Name", "")
        hood = get_neighborhood_from_address(name, use_geocoding=True)
        if hood:
            deal["Neighborhood"] = hood
            geocoded += 1
            logger.info(f"  [{count+1}/{len(needs_geocoding)}] ✅ {name} → {hood}")
        else:
            logger.info(f"  [{count+1}/{len(needs_geocoding)}] ❌ {name} → No neighborhood found")

        if (count + 1) % 25 == 0:
            # Save progress periodically
            cache_data["deals"] = deals
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"  Progress saved ({count+1}/{len(needs_geocoding)})")

    total_matched = local_matched + geocoded
    logger.info(f"\nFinal results: {total_matched}/{len(deals)} deals have neighborhoods")
    logger.info(f"  Local: {local_matched}, Geocoded: {geocoded}, Unresolved: {len(deals) - total_matched}")

    # Save final results
    cache_data["deals"] = deals
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=2)
    logger.info("Cache updated with neighborhood data")

    # Print summary by neighborhood
    hood_counts = {}
    for deal in deals:
        h = deal.get("Neighborhood")
        if h:
            hood_counts[h] = hood_counts.get(h, 0) + 1

    logger.info(f"\nNeighborhood distribution ({len(hood_counts)} neighborhoods):")
    for hood, count in sorted(hood_counts.items(), key=lambda x: -x[1]):
        logger.info(f"  {hood}: {count} deals")


if __name__ == "__main__":
    main()
