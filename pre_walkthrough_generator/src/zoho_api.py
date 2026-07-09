"""
Zoho CRM API Integration
Handles authentication and data fetching from Zoho CRM
"""

import requests
import json
import time
import re
import html
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
            # Send credentials in the POST BODY (data=), never the query string —
            # otherwise client_secret/refresh_token land in the request URL and a
            # raised HTTPError (which echoes the URL) leaks them into the logs.
            response = requests.post(self.auth_url, data=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self.access_token = data.get("access_token")
            if not self.access_token:
                raise ValueError("Zoho token response did not include an access_token")
            # Zoho tokens typically expire in 1 hour. Coerce defensively and never
            # let the buffer push the expiry into the past.
            try:
                expires_in = int(data.get("expires_in", 3600))
            except (TypeError, ValueError):
                expires_in = 3600
            self.token_expires_at = datetime.now() + timedelta(seconds=max(0, expires_in - 300))  # 5 min buffer
            
            logger.info("Zoho access token refreshed successfully")
            return self.access_token
            
        except Exception as e:
            # Log only the exception TYPE — the message can carry the auth URL/creds.
            logger.error("Error refreshing Zoho token: %s", type(e).__name__)
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
            # Zoho returns 204 No Content (empty body) when a search/related-list
            # has no records — that's a normal "not found", not an error.
            if response.status_code == 204 or not response.content:
                return {}
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
        # Sanitize the value so characters that are significant in COQL criteria
        # (parentheses, colons) can't break the query syntax.
        safe = str(neighborhood).replace('(', ' ').replace(')', ' ').replace(':', ' ').strip()
        criteria = f"(Neighborhood:equals:{safe})"
        return self.search_records(module_name, criteria)

    @staticmethod
    def _coql_safe(value: str) -> str:
        """Strip characters that would break a COQL criteria value."""
        v = str(value or "")
        for ch in ('(', ')', ':', '#', '\\', '"', ','):
            v = v.replace(ch, ' ')
        return ' '.join(v.split())

    @staticmethod
    def _strip_html(text: str, max_len: int = 2000) -> str:
        """Zoho notes are stored as HTML — convert to clean plain text for the report."""
        s = str(text or "")
        s = re.sub(r'(?i)<\s*(br|/p|/li|/div|/tr|/h[1-6])\s*/?>', '\n', s)
        s = re.sub(r'<[^>]+>', '', s)
        s = html.unescape(s)
        s = re.sub(r'[ \t]+', ' ', s)
        s = re.sub(r'\n\s*\n+', '\n', s).strip()
        if len(s) > max_len:
            s = s[:max_len].rstrip() + '…'
        return s

    def _notes_for_record(self, module_name: str, record_id: str, seen: set, out: List[str]) -> None:
        """Append a record's note contents (as 'Title: Content' strings) into ``out``, deduped."""
        try:
            data = self._make_request(f"{module_name}/{record_id}/Notes")
            for n in (data.get("data", []) if isinstance(data, dict) else []):
                title = self._strip_html(n.get("Note_Title") or "", max_len=200)
                content = self._strip_html(n.get("Note_Content") or "")
                txt = f"{title}: {content}" if title and content else (content or title)
                txt = txt.strip()
                if txt and txt not in seen:
                    seen.add(txt)
                    out.append(txt)
        except Exception as e:
            logger.warning("Could not fetch notes for %s/%s: %s", module_name, record_id, e)

    def get_relevant_notes(self, address: str = None, contact_name: str = None,
                           max_notes: int = 10) -> List[str]:
        """Gather CRM notes relevant to this walkthrough.

        Notes live on both Deals and Contacts. Primary (precise) path: match the
        Deal by address, pull the Deal's notes AND its linked Contact's notes.
        Fallback: if no deal matched and a client name is known, match the Contact
        by exact first+last name. Returns deduped 'Title: Content' strings, or [].
        Never raises.
        """
        out: List[str] = []
        seen: set = set()
        try:
            # 1. Deal by address -> deal notes + linked-contact notes.
            #    Only trust a UNIQUE match, or an EXACT street match among several;
            #    if the address is ambiguous (matches multiple unrelated deals),
            #    SKIP rather than guess deals[0] — guessing could surface a
            #    different party's private CRM notes.
            deal_matched = False
            street = self._coql_safe(str(address or "").split(',')[0])
            if len(street) >= 3:
                deals = self.search_records("Deals", f"(Deal_Name:starts_with:{street})",
                                            fields=["Deal_Name", "Contact_Name"])
                chosen = None
                if len(deals) == 1:
                    chosen = deals[0]
                elif len(deals) > 1:
                    exact = [d for d in deals
                             if self._coql_safe(str(d.get("Deal_Name", ""))).lower() == street.lower()]
                    chosen = exact[0] if len(exact) == 1 else None
                    if not chosen:
                        logger.info("Ambiguous deal match for %r (%d candidates) — skipping deal notes",
                                    address, len(deals))
                if chosen:
                    deal_matched = True
                    if chosen.get("id"):
                        self._notes_for_record("Deals", chosen["id"], seen, out)
                    cn = chosen.get("Contact_Name")
                    if isinstance(cn, dict) and cn.get("id"):
                        self._notes_for_record("Contacts", cn["id"], seen, out)

            # 2. Fallback: exact contact-name match (only if the deal path found nothing)
            if not out and contact_name:
                parts = self._coql_safe(contact_name).split()
                if len(parts) >= 2:
                    first, last = parts[0], parts[-1]
                    contacts = self.search_records(
                        "Contacts", f"((Last_Name:equals:{last})and(First_Name:equals:{first}))",
                        fields=["Full_Name"])
                    if contacts and contacts[0].get("id"):
                        self._notes_for_record("Contacts", contacts[0]["id"], seen, out)

            logger.info("Fetched %d CRM note(s) for address=%r contact=%r (deal_matched=%s)",
                        len(out), address, contact_name, deal_matched)
            return out[:max_notes]
        except Exception as e:
            logger.warning("Could not fetch CRM notes (address=%r, contact=%r): %s", address, contact_name, e)
            return out[:max_notes]
