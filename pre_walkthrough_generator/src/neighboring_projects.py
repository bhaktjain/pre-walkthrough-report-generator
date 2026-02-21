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
        self.cache_ttl_hours = 6  # Refresh every 6 hours
        
    def _extract_neighborhood_from_address(self, address: str) -> Optional[str]:
        """
        Extract neighborhood from address string
        For NYC addresses, we'll use zip code or borough
        """
        # Extract zip code
        zip_match = re.search(r'\b(\d{5})\b', address)
        if zip_match:
            return zip_match.group(1)
        
        # Extract borough/neighborhood
        nyc_neighborhoods = [
            'Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island',
            'Flatiron', 'Chelsea', 'Midtown', 'Upper East Side', 'Upper West Side',
            'Lower East Side', 'SoHo', 'Tribeca', 'Greenwich Village', 'East Village',
            'Williamsburg', 'Park Slope', 'DUMBO', 'Long Island City'
        ]
        
        address_lower = address.lower()
        for neighborhood in nyc_neighborhoods:
            if neighborhood.lower() in address_lower:
                return neighborhood
        
        return None
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for comparison"""
        if not address:
            return ""
        
        # Convert to lowercase
        addr = address.lower().strip()
        
        # Remove apartment/unit numbers
        addr = re.sub(r'\s*[#,]?\s*(apt|apartment|unit)\s*[a-zA-Z0-9]+', '', addr, flags=re.IGNORECASE)
        addr = re.sub(r'\s*#[a-zA-Z0-9]+', '', addr)
        
        # Normalize street abbreviations
        replacements = {
            ' street': ' st',
            ' avenue': ' ave',
            ' road': ' rd',
            ' boulevard': ' blvd',
            ' place': ' pl',
            ' west ': ' w ',
            ' east ': ' e ',
            ' north ': ' n ',
            ' south ': ' s ',
        }
        
        for old, new in replacements.items():
            addr = addr.replace(old, new)
        
        # Remove extra spaces
        addr = ' '.join(addr.split())
        
        return addr
    
    def _is_same_building(self, address1: str, address2: str) -> bool:
        """Check if two addresses are in the same building"""
        norm1 = self._normalize_address(address1)
        norm2 = self._normalize_address(address2)
        
        if not norm1 or not norm2:
            return False
        
        # Extract street address (without unit)
        # e.g., "16 w 21st st" from "16 w 21st st apt 5a"
        street1 = norm1.split(',')[0].strip()
        street2 = norm2.split(',')[0].strip()
        
        return street1 == street2
    
    def _is_same_neighborhood(self, address1: str, address2: str, 
                             neighborhood1: str = None, neighborhood2: str = None) -> bool:
        """Check if two addresses are in the same neighborhood"""
        # First try explicit neighborhoods
        if neighborhood1 and neighborhood2:
            return neighborhood1.lower() == neighborhood2.lower()
        
        # Extract neighborhoods from addresses
        n1 = neighborhood1 or self._extract_neighborhood_from_address(address1)
        n2 = neighborhood2 or self._extract_neighborhood_from_address(address2)
        
        if n1 and n2:
            return n1.lower() == n2.lower()
        
        return False
    
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
            
            # Check if cache is still valid
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
        cache_data = self.load_cache()
        return cache_data is not None
    
    def find_neighboring_projects(self, target_address: str, 
                                 target_neighborhood: str = None,
                                 same_building_only: bool = False) -> List[Dict[str, Any]]:
        """
        Find neighboring projects from cache
        
        Args:
            target_address: Address to search around
            target_neighborhood: Neighborhood name (optional)
            same_building_only: Only return projects in same building
            
        Returns:
            List of neighboring project dictionaries with:
            - deal_name: Project name
            - address: Project address
            - amount: Deal amount
            - stage: Deal stage/status
            - is_same_building: Boolean flag
        """
        cache_data = self.load_cache()
        
        if not cache_data:
            logger.warning("No valid cache available")
            return []
        
        deals = cache_data.get("deals", [])
        neighboring = []
        
        for deal in deals:
            deal_name = deal.get("Deal_Name", "")
            
            # Skip if no deal name (likely not a valid project)
            if not deal_name:
                continue
            
            # Extract address from deal name (assuming format like "111 Glenview Road")
            # You may need to adjust this based on your actual data format
            deal_address = deal_name
            
            # Check if same building
            is_same_bldg = self._is_same_building(target_address, deal_address)
            
            # Check if same neighborhood
            is_same_neigh = self._is_same_neighborhood(
                target_address, deal_address,
                target_neighborhood, None
            )
            
            # Apply filters
            if same_building_only and not is_same_bldg:
                continue
            
            if not same_building_only and not is_same_neigh and not is_same_bldg:
                continue
            
            # Format the project data
            project = {
                "deal_name": deal_name,
                "address": deal_address,
                "amount": deal.get("Amount", 0),
                "stage": deal.get("Stage", "Unknown"),
                "is_same_building": is_same_bldg,
                "contact_name": deal.get("Contact_Name", {}).get("name", "") if isinstance(deal.get("Contact_Name"), dict) else "",
                "closing_date": deal.get("Closing_Date", "")
            }
            
            neighboring.append(project)
        
        # Sort by same building first, then by amount
        neighboring.sort(key=lambda x: (not x["is_same_building"], -x.get("amount", 0)))
        
        logger.info(f"Found {len(neighboring)} neighboring projects for {target_address}")
        return neighboring
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_data = self.load_cache()
        
        if not cache_data:
            return {
                "exists": False,
                "valid": False,
                "count": 0,
                "age": None
            }
        
        timestamp = datetime.fromisoformat(cache_data["timestamp"])
        age = datetime.now() - timestamp
        
        return {
            "exists": True,
            "valid": age <= timedelta(hours=self.cache_ttl_hours),
            "count": cache_data["count"],
            "age_hours": age.total_seconds() / 3600,
            "last_updated": timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
