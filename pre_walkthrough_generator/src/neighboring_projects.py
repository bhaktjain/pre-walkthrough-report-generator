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

# Import neighborhood-resolution helpers once, at module load, so an import
# failure is logged loudly instead of being silently swallowed on every call
# (which previously degraded matching to "same building only" with no signal).
try:
    from nyc_neighborhoods import (
        get_neighborhood_from_address,
        get_locality,
        enrich_deals_with_neighborhoods,
    )
except ImportError:
    try:
        from pre_walkthrough_generator.src.nyc_neighborhoods import (
            get_neighborhood_from_address,
            get_locality,
            enrich_deals_with_neighborhoods,
        )
    except ImportError as _imp_err:  # pragma: no cover
        get_neighborhood_from_address = None
        get_locality = None
        enrich_deals_with_neighborhoods = None
        logger.error(
            "Could not import nyc_neighborhoods — neighborhood matching disabled: %s",
            _imp_err,
        )


class NeighboringProjectsManager:
    """Manages neighboring projects cache and matching logic"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "zoho_deals_cache.json"
        self.cache_ttl_hours = 48  # Consider the cache stale after 2 days (auto-refreshed on a timer)

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

    def _read_cache_file(self) -> Optional[Dict[str, Any]]:
        """Read and parse the raw cache file (no freshness check)."""
        if not self.cache_file.exists():
            return None
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading cache file: {e}")
            return None

    def _cache_age(self, cache_data: Dict[str, Any]) -> Optional[timedelta]:
        try:
            return datetime.now() - datetime.fromisoformat(cache_data["timestamp"])
        except Exception:
            return None

    def save_cache(self, deals: List[Dict[str, Any]], preserve_neighborhoods: bool = True) -> None:
        """Save deals to cache file.

        When ``preserve_neighborhoods`` is set, carry forward any ``Neighborhood``
        tags from the existing cache (matched by ``Deal_Name``) onto incoming deals
        that lack one. This prevents a raw re-sync (which fetches deals without a
        ``Neighborhood`` field) from wiping previously-computed neighborhoods.
        """
        if preserve_neighborhoods:
            try:
                existing = self._read_cache_file()
                if existing:
                    prior = {
                        d.get("Deal_Name"): d.get("Neighborhood")
                        for d in existing.get("deals", [])
                        if d.get("Deal_Name") and d.get("Neighborhood")
                    }
                    for deal in deals:
                        if not deal.get("Neighborhood"):
                            carried = prior.get(deal.get("Deal_Name"))
                            if carried:
                                deal["Neighborhood"] = carried
            except Exception as e:
                logger.warning(f"Could not carry forward neighborhoods: {e}")

        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "deals": deals,
            "count": len(deals)
        }
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            tagged = sum(1 for d in deals if d.get("Neighborhood"))
            logger.info(f"Saved {len(deals)} deals to cache ({tagged} with neighborhood)")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def load_cache(self) -> Optional[Dict[str, Any]]:
        """Load deals from cache.

        Returns the cached data even when it is past its TTL — a stale cache is
        far more useful than zero neighboring projects. Staleness is logged and is
        surfaced separately via :meth:`is_cache_fresh` / :meth:`get_cache_stats`,
        so callers (e.g. the startup sync) can decide whether to refresh.
        Returns ``None`` only when the cache is missing or corrupt.
        """
        cache_data = self._read_cache_file()
        if not cache_data:
            logger.info("Cache file does not exist or is unreadable")
            return None
        age = self._cache_age(cache_data)
        if age is not None and age > timedelta(hours=self.cache_ttl_hours):
            logger.warning(
                f"Cache is stale (age: {age}) — using it anyway; a refresh is recommended"
            )
        logger.info(f"Loaded {cache_data.get('count')} deals from cache (age: {age})")
        return cache_data

    def is_cache_fresh(self) -> bool:
        """True if the cache exists and is within its TTL."""
        cache_data = self._read_cache_file()
        if not cache_data:
            return False
        age = self._cache_age(cache_data)
        return age is not None and age <= timedelta(hours=self.cache_ttl_hours)

    def is_cache_valid(self) -> bool:
        """Backwards-compatible alias for :meth:`is_cache_fresh`."""
        return self.is_cache_fresh()

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

        # Determine the target locality with the same resolver used to tag the
        # cached deals, so both sides share one vocabulary: a NYC neighborhood
        # inside the five boroughs, else "City, ST" (NJ/CT/Miami/Westchester/Hamptons).
        zip_neighborhood = None
        if get_locality is not None:
            try:
                zip_neighborhood = get_locality(target_address, use_geocoding=False)
            except Exception as e:
                logger.error(f"Locality lookup failed for {target_address}: {e}")
        else:
            logger.warning(
                "nyc_neighborhoods unavailable — falling back to same-building matching only"
            )

        # Use ZIP-based neighborhood as primary (matches our cache),
        # fall back to provided neighborhood from API
        if zip_neighborhood:
            target_neighborhood = zip_neighborhood
        elif not target_neighborhood or target_neighborhood == 'Information not available':
            target_neighborhood = None

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
