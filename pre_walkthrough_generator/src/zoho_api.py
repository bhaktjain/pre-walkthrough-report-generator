"""
Zoho CRM API Integration
Handles authentication and data fetching from Zoho CRM
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ZohoAPI:
    """Zoho CRM API client with OAuth2 authentication"""
    
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
        self.token_expires_at = None
        self.base_url = "https://www.zohoapis.com/crm/v2"
        self.auth_url = "https://accounts.zoho.com/oauth/v2/token"
        
    def _get_access_token(self) -> str:
        """Get or refresh access token"""
        # Check if we have a valid token
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token
        
        # Refresh the token
        logger.info("Refreshing Zoho access token...")
        params = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        
        try:
            response = requests.post(self.auth_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self.access_token = data["access_token"]
            # Zoho tokens typically expire in 1 hour
            expires_in = data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
            
            logger.info("Zoho access token refreshed successfully")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Error refreshing Zoho token: {e}")
            raise
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make authenticated request to Zoho CRM API"""
        access_token = self._get_access_token()
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error making Zoho API request to {endpoint}: {e}")
            raise
    
    def get_all_records(self, module_name: str, fields: List[str] = None, 
                       max_records: int = 5000) -> List[Dict[str, Any]]:
        """
        Fetch all records from a Zoho CRM module
        
        Args:
            module_name: Name of the module (e.g., "Deals", "Projects")
            fields: List of field names to fetch (None = all fields)
            max_records: Maximum number of records to fetch
            
        Returns:
            List of record dictionaries
        """
        logger.info(f"Fetching records from Zoho CRM module: {module_name}")
        
        all_records = []
        page = 1
        per_page = 200  # Zoho max per page
        
        while len(all_records) < max_records:
            params = {
                "page": page,
                "per_page": per_page
            }
            
            if fields:
                params["fields"] = ",".join(fields)
            
            try:
                data = self._make_request(module_name, params)
                
                if "data" not in data or not data["data"]:
                    break
                
                records = data["data"]
                all_records.extend(records)
                
                logger.info(f"Fetched page {page}: {len(records)} records")
                
                # Check if there are more pages
                info = data.get("info", {})
                if not info.get("more_records", False):
                    break
                
                page += 1
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        logger.info(f"Total records fetched: {len(all_records)}")
        return all_records[:max_records]
    
    def search_records(self, module_name: str, criteria: str, 
                      fields: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search records in Zoho CRM using COQL (Zoho Query Language)
        
        Args:
            module_name: Name of the module
            criteria: Search criteria (e.g., "(City:equals:New York)")
            fields: List of field names to fetch
            
        Returns:
            List of matching records
        """
        logger.info(f"Searching {module_name} with criteria: {criteria}")
        
        params = {
            "criteria": criteria
        }
        
        if fields:
            params["fields"] = ",".join(fields)
        
        try:
            data = self._make_request(f"{module_name}/search", params)
            records = data.get("data", [])
            logger.info(f"Found {len(records)} matching records")
            return records
        except Exception as e:
            logger.error(f"Error searching records: {e}")
            return []
    
    def get_projects_by_neighborhood(self, neighborhood: str, 
                                    module_name: str = "Deals") -> List[Dict[str, Any]]:
        """
        Get all projects in a specific neighborhood
        
        Args:
            neighborhood: Neighborhood name (e.g., "Flatiron District")
            module_name: Zoho module name
            
        Returns:
            List of project records
        """
        # This will be customized based on your Zoho field structure
        criteria = f"(Neighborhood:equals:{neighborhood})"
        return self.search_records(module_name, criteria)
