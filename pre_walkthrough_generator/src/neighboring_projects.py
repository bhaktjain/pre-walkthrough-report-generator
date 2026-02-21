"""
Neighboring Projects Manager
Handles caching and matching of Zoho CRM deals by neighborhood
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)


class NeighboringProjectsManager:
    """Manages neighboring projects cache and matching logic"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "zoho_deals_cache.json"
        self.cache_ttl_hours = 168  # Refresh every 1 week (7 days * 24 hours)

    def _normalize_address(self, address: str) -> str:
        """Normalize address for comparison"""
        if not address:
            return ""
        addr = address.lower().strip()
        # Remove apartment/unit numbers
        addr = re.sub(r'\s*[,]?\s*[#]?\s*(apt\.?|apartment|unit)\s+[#]?\s*[a-zA-Z0-9/\-]+', '', addr, flags=re.IGNORECASE)
        addr = re.sub(r'\s+unit\s+[a-zA-Z0-9/\-]+', '', addr, flags=re.IGNORECASE)
        addr = re.sub(r'\s*[,]?\s*#[a-zA-Z0-9/\-]+', '', addr)
        # Normalize street abbreviations
        replacements = {
            ' street': ' st', ' avenue': ' ave', ' road': ' rd',
            ' boulevard': ' blvd', ' place': ' pl',
            ' west ': ' w ', ' east ': ' e ',
            ' north ': ' n ', ' south ': ' s ',
        }
        for old, new in replacements.items():
            addr = addr.replace(old, new)
        addr = ' '.join(addr.split())
        return addr

    def _is_same_building(self, address1: str, address2: str) -> bool:
        """Check if two addresses are in the same building"""
        norm1 = self._normalize_address(address1)
        norm2 = self._normalize_address(address2)
        if not norm1 or not norm2:
            return False
        street1 = norm1.split(',')[0].strip()
        street2 = norm2.split(',')[0].strip()
        return street1 == street2

    def save_cache(self, deals: List[Dict[str, Any]]) -> None:
        """Save deals to cache file"""
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "deals": deals,
            "count": len(deals)
        }
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Saved {len(deals)} deals to cache")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def load_cache(self) -> Optional[Dict[str, Any]]:
        """Load deals from cache file"""
        if not self.cache_file.exists():
            logger.info("Cache file does not exist")
            return None
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            timestamp = datetime.fromisoformat(cache_data["timestamp"])
            age = datetime.now() - timestamp
            if age > timedelta(hours=self.cache_ttl_hours):
                logger.info(f"Cache is stale (age: {age})")
                return None
            logger.info(f"Loaded {cache_data['count']} deals from cache (age: {age})")
            return cache_data
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return None

    def is_cache_valid(self) -> bool:
        """Check if cache exists and is still valid"""
        return self.load_cache() is not None

    def find_neighboring_projects(self, target_address: str,
                                 target_neighborhood: str = None,
                                 same_building_only: bool = False) -> List[Dict[str, Any]]:
        """
        Find neighboring projects from cache using NEIGHBORHOOD matching.
        
        Strategy:
        1. Determine the target address's neighborhood
        2. For each cached deal, check its stored Neighborhood field
        3. Match deals that share the same neighborhood
        4. Same-building matches are always included and flagged
        
        Args:
            target_address: Address to search around
            target_neighborhood: Neighborhood name (from property details or computed)
            same_building_only: Only return projects in same building
        """
        cache_data = self.load_cache()
        if not cache_data:
            logger.warning("No valid cache available")
            return []

        deals = cache_data.get("deals", [])

        # Determine target neighborhood
        # Use provided neighborhood, or look it up
        if not target_neighborhood or target_neighborhood == 'Information not available':
            try:
                from nyc_neighborhoods import get_neighborhood_from_address
                target_neighborhood = get_neighborhood_from_address(target_address, use_geocoding=False)
            except ImportError:
                pass

        if target_neighborhood:
            target_hood_lower = target_neighborhood.lower().strip()
            logger.info(f"Target neighborhood: {target_neighborhood}")
        else:
            target_hood_lower = None
            logger.warning(f"Could not determine neighborhood for: {target_address}")

        neighboring = []
        for deal in deals:
            deal_name = deal.get("Deal_Name", "")
            if not deal_name:
                continue

            deal_address = deal_name
            deal_neighborhood = deal.get("Neighborhood")

            # Check same building
            is_same_bldg = self._is_same_building(target_address, deal_address)

            # Check same neighborhood
            is_same_hood = False
            if target_hood_lower and deal_neighborhood:
                deal_hood_lower = deal_neighborhood.lower().strip()
                is_same_hood = (target_hood_lower == deal_hood_lower)

            # Apply filters
            if same_building_only and not is_same_bldg:
                continue
            if not same_building_only and not is_same_hood and not is_same_bldg:
                continue

            project = {
                "deal_name": deal_name,
                "address": deal_address,
                "amount": deal.get("Amount", 0),
                "stage": deal.get("Stage", "Unknown"),
                "is_same_building": is_same_bldg,
                "neighborhood": deal_neighborhood,
                "contact_name": deal.get("Contact_Name", {}).get("name", "") if isinstance(deal.get("Contact_Name"), dict) else "",
                "closing_date": deal.get("Closing_Date", "")
            }
            neighboring.append(project)

        # Sort: same building first, then by amount descending
        neighboring.sort(key=lambda x: (not x["is_same_building"], -(x.get("amount") or 0)))

        logger.info(f"Found {len(neighboring)} neighboring projects for {target_address} "
                    f"(neighborhood: {target_neighborhood})")
        return neighboring

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_data = self.load_cache()
        if not cache_data:
            return {"exists": False, "valid": False, "count": 0, "age": None}

        timestamp = datetime.fromisoformat(cache_data["timestamp"])
        age = datetime.now() - timestamp

        # Count deals with neighborhoods
        deals = cache_data.get("deals", [])
        with_hood = sum(1 for d in deals if d.get("Neighborhood"))

        return {
            "exists": True,
            "valid": age <= timedelta(hours=self.cache_ttl_hours),
            "count": cache_data["count"],
            "deals_with_neighborhood": with_hood,
            "age_hours": age.total_seconds() / 3600,
            "last_updated": timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
