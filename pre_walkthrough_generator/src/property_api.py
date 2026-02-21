import requests
import re
from typing import Dict, Any, Optional
import time
import http.client
import json
from openai import OpenAI
import urllib.parse
import logging

# Try to import BeautifulSoup4, but make it optional for deployment
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    BeautifulSoup = None
    HAS_BS4 = False
    print("Warning: BeautifulSoup4 not available. Web scraping features will be disabled.")

logger = logging.getLogger(__name__)

class PropertyAPI:
    def __init__(self, api_key: str, openai_api_key: str = None, serpapi_key: str = None):
        self.api_key = api_key
        self.openai_api_key = openai_api_key
        self.serpapi_key = serpapi_key
        self.host = "us-real-estate-listings.p.rapidapi.com"
        self.headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': self.host
        }
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
        logger.info("PropertyAPI initialized")

    def _make_request(self, endpoint: str, params: Dict[str, str] = None) -> Optional[Dict]:
        """Make a request to the RapidAPI endpoint"""
        try:
            conn = http.client.HTTPSConnection(self.host)
            
            # Build query string if params provided
            query = ""
            if params:
                # URL encode each parameter value
                encoded_params = {k: urllib.parse.quote(str(v)) for k, v in params.items()}
                query = "?" + "&".join(f"{k}={v}" for k, v in encoded_params.items())
            
            conn.request("GET", f"{endpoint}{query}", headers=self.headers)
            res = conn.getresponse()
            data = res.read()
            
            if res.status != 200:
                print(f"Error from API: {res.status}")
                print(f"Response: {data.decode('utf-8')}")
                return None
                
            return json.loads(data.decode('utf-8'))
            
        except Exception as e:
            print(f"Error making request: {e}")
            return None
        finally:
            conn.close()

    def format_address_for_search(self, address: str) -> str:
        """Format address for property search"""
        # Remove quotes and clean whitespace
        address = address.replace('"', '').strip()
        
        # Extract components
        match = re.match(r'(\d+)\s+West\s+(\d+)(?:st|nd|rd|th)\s+Street(?:\s*,\s*Apt\s+\w+)?(?:\s*,\s*New\s+York(?:\s*,\s*NY)?)?', address, re.IGNORECASE)
        if match:
            street_num = match.group(1)
            street_name = match.group(2)
            return f"{street_num} W {street_name}th St, New York, NY"
        
        return address

    def get_property_id_from_openai(self, address: str) -> Optional[str]:
        """Use OpenAI to get the property ID or MLS ID - Currently disabled as OpenAI doesn't have real-time MLS access"""
        # OpenAI doesn't actually have access to real-time MLS databases or web search
        # This method is disabled to avoid false expectations
        logger.info("OpenAI property ID lookup is disabled - OpenAI doesn't have real-time MLS access")
        return None

    def get_property_details(self, property_id: str) -> Dict[str, Any]:
        """Get detailed property information using property ID (live RapidAPI)."""
        import re
        try:
            print(f"Fetching details for property ID: {property_id}")
            data = self._make_request("/v2/property", {"id": property_id})
            print("\n[DEBUG] Raw API response type:", type(data))
            if isinstance(data, dict):
                print("[DEBUG] Raw API response keys:", list(data.keys()))
            print("[DEBUG] /v2/property API response:")
            print(json.dumps(data, indent=2))
            if not data or 'data' not in data or not data['data']:
                print("[ERROR] API response missing 'data' key or property data is empty. Full response:")
                print(data)
                return {}
            d = data['data']

            def search_details(category=None, regex=None, contains=None):
                details_list = d.get('details') or []
                for det in details_list:
                    if category and det.get('category', '').lower() == category.lower():
                        text_list = det.get('text') or []
                        for t in text_list:
                            if regex:
                                m = re.search(regex, t)
                                if m:
                                    return m.group(1)
                            elif contains and contains.lower() in t.lower():
                                return t
                            else:
                                return t
                    text_list = det.get('text') or []
                    for t in text_list:
                        if contains and contains.lower() in t.lower():
                            return t
                        if regex:
                            m = re.search(regex, t)
                            if m:
                                return m.group(1)
                return None

            def search_details_any(regex):
                details_list = d.get('details') or []
                for det in details_list:
                    text_list = det.get('text') or []
                    for t in text_list:
                        m = re.search(regex, t)
                        if m:
                            return m.group(1)
                return None

            # Address fields
            # Safely handle cases where 'location' or 'address' may be None instead of a dict
            location_obj = d.get('location') or {}
            address_obj = location_obj.get('address') or {}
            address = address_obj.get('line') or (
                f"{address_obj.get('street_number', '')} {address_obj.get('street_name', '')} {address_obj.get('street_suffix', '')} {address_obj.get('unit', '')}".strip()
            )
            city = address_obj.get('city')
            state = address_obj.get('state_code') or address_obj.get('state')
            zip_code = address_obj.get('postal_code')

            # Price
            price = d.get('list_price')
            if not price:
                price = search_details_any(r'Price: \$?([\d,]+)')
                if price:
                    price = int(price.replace(',', ''))
            print(f"[DEBUG] Price: {price}")

            # Last sold price and date
            last_sold_price = d.get('last_sold_price')
            last_sold_date = d.get('last_sold_date')
            # Try property_history
            if not last_sold_price or not last_sold_date:
                for hist in (d.get('property_history') or []):
                    if hist.get('event_name', '').lower() in ['sold', 'sold (public record)']:
                        if not last_sold_price and 'price' in hist:
                            last_sold_price = hist['price']
                        if not last_sold_date and 'date' in hist:
                            last_sold_date = hist['date']
                        if last_sold_price and last_sold_date:
                            break
            print(f"[DEBUG] Last Sold Price: {last_sold_price}")
            print(f"[DEBUG] Last Sold Date: {last_sold_date}")

            # Bedrooms
            description = d.get('description') or {}
            bedrooms = description.get('beds')
            if not bedrooms:
                bedrooms = search_details('Bedrooms', r'Bedrooms: (\d+)')
            if not bedrooms:
                bedrooms = search_details_any(r'Bedrooms: (\d+)')
            if not bedrooms:
                bedrooms = search_details_any(r'Beds: (\d+)')
            if not bedrooms:
                bedrooms = search_details_any(r'Bedroom[s]?: (\d+)')
            if not bedrooms:
                bedrooms = 'Information not available'
            print(f"[DEBUG] Bedrooms: {bedrooms}")

            # Bathrooms
            bathrooms = description.get('baths') or description.get('baths_consolidated')
            if not bathrooms:
                bathrooms = search_details('Bathrooms', r'Bathrooms: (\d+)')
            if not bathrooms:
                bathrooms = search_details_any(r'Bathrooms: (\d+)')
            if not bathrooms:
                bathrooms = search_details_any(r'Baths: (\d+)')
            if not bathrooms:
                bathrooms = search_details_any(r'Bathroom[s]?: (\d+)')
            if not bathrooms:
                bathrooms = 'Information not available'
            print(f"[DEBUG] Bathrooms: {bathrooms}")

            # Rooms (total rooms)
            rooms = search_details('Other Rooms', r'Total Rooms: (\d+)')
            if not rooms:
                rooms = search_details_any(r'Total Rooms: (\d+)')
            if not rooms:
                rooms = 'Information not available'
            print(f"[DEBUG] Rooms: {rooms}")

            # Sqft
            sqft = description.get('sqft')
            if not sqft:
                sqft = search_details_any(r'(\d{3,5})\s*sqft')
            if not sqft:
                # Try property_history
                for hist in (d.get('property_history') or []):
                    listing = hist.get('listing') or {}
                    desc = listing.get('description') or {}
                    if desc and desc.get('sqft'):
                        sqft = desc['sqft']
                        break
            if not sqft:
                sqft = 'Information not available'
            print(f"[DEBUG] Sqft: {sqft}")

            # Year Built
            year_built = description.get('year_built')
            if not year_built:
                year_built = search_details_any(r'Year Built: (\d{4})')
            if not year_built:
                year_built = 'Information not available'
            print(f"[DEBUG] Year Built: {year_built}")

            # HOA Fee
            # 'hoa' may be explicitly set to null which breaks chained .get calls
            hoa_obj = d.get('hoa') or {}
            hoa_fee = hoa_obj.get('fee')
            if not hoa_fee:
                hoa_fee = search_details('Homeowners Association', r'Association Fee: (\d+)')
            if not hoa_fee:
                hoa_fee = search_details_any(r'Association Fee: (\d+)')
            if not hoa_fee:
                hoa_fee = 'Information not available'
            print(f"[DEBUG] HOA Fee: {hoa_fee}")

            # Property Type
            property_type = description.get('type') or description.get('sub_type')
            if not property_type:
                property_type = search_details_any(r'Property Subtype: ([\w-]+)')
            if not property_type:
                details_list = d.get('details') or []
                for det in details_list:
                    text_list = det.get('text') or []
                    for t in text_list:
                        if 'property subtype' in t.lower():
                            property_type = t.split(':')[-1].strip()
                            break
            if not property_type:
                property_type = 'Information not available'
            print(f"[DEBUG] Property Type: {property_type}")

            # Neighborhood
            neighborhood = None
            neighborhoods = (d.get('location') or {}).get('neighborhoods') or []
            if neighborhoods:
                neighborhood = neighborhoods[0].get('name')
            if not neighborhood:
                neighborhood = search_details_any(r'Neighborhood: ([\w\s-]+)')
            if not neighborhood:
                details_list = d.get('details') or []
                for det in details_list:
                    text_list = det.get('text') or []
                    for t in text_list:
                        if 'neighborhood' in t.lower():
                            neighborhood = t.split(':')[-1].strip()
                            break
            if not neighborhood:
                neighborhood = 'Information not available'
            print(f"[DEBUG] Neighborhood: {neighborhood}")

            # Photos and floor plans
            photos = []
            floor_plans = []
            try:
                photos_list = d.get('photos') or []
                for photo in photos_list:
                    if not photo:
                        continue
                    href = photo.get('href')
                    if not href:
                        continue
                    tags = [tag.get('label', '') for tag in (photo.get('tags') or []) if tag and tag.get('label')]
                    if 'floor_plan' in tags:
                        floor_plans.append({"url": href, "description": "floor_plan"})
                    else:
                        photos.append({"url": href, "description": "photo"})
            except Exception as photo_error:
                print(f"[DEBUG] Error processing photos: {photo_error}")
                photos = []
                floor_plans = []

            # Check for URL in API response
            listing_url = None
            # Look for URL in various possible locations in the API response
            if 'href' in d:
                listing_url = d['href']
            elif 'url' in d:
                listing_url = d['url']
            elif 'listing_url' in d:
                listing_url = d['listing_url']
            elif 'realtor_url' in d:
                listing_url = d['realtor_url']
            elif 'permalink' in d:
                listing_url = d['permalink']
            elif 'web_url' in d:
                listing_url = d['web_url']
            
            # Also check in nested objects
            if not listing_url:
                for key in ['listing', 'property', 'details']:
                    if key in d and isinstance(d[key], dict):
                        nested = d[key]
                        for url_key in ['href', 'url', 'listing_url', 'realtor_url', 'permalink', 'web_url']:
                            if url_key in nested:
                                listing_url = nested[url_key]
                                break
                        if listing_url:
                            break
            
            print(f"[DEBUG] Found listing URL in API response: {listing_url}")

            details = {
                'address': address or 'Information not available',
                'city': city or 'Information not available',
                'state': state or 'Information not available',
                'zip': zip_code or 'Information not available',
                'price': price or 'Information not available',
                'last_sold_price': last_sold_price or 'Information not available',
                'last_sold_date': last_sold_date or 'Information not available',
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'rooms': rooms,
                'sqft': sqft,
                'year_built': year_built,
                'hoa_fee': hoa_fee,
                'property_type': property_type,
                'neighborhood': neighborhood,
                'photos': photos,
                'floor_plans': floor_plans,
                'listing_url': listing_url  # Add the URL from API response
            }
            print("\n[DEBUG] Extracted property details to return:")
            print(json.dumps(details, indent=2, default=str))
            return details
        except Exception as e:
            print(f"Error in get_property_details: {e}")
            return {}

    def get_property_photos(self, property_id: str) -> Dict[str, Any]:
        """Fetch property photos via RapidAPI and separate floor plans."""
        try:
            if not self.api_key:
                return {"images": [], "floor_plans": []}

            print(f"Fetching photos for property ID: {property_id}")
            res = self._make_request("/propertyPhotos", {"id": property_id})
            print("\n[DEBUG] /propertyPhotos API response:")
            print(json.dumps(res, indent=2))
            if not res or ("photos" not in res and "data" not in res):
                return {"images": [], "floor_plans": []}

            images = res.get("photos") or res.get("data", {}).get("homeImages", [])
            all_imgs = []
            floor_plans = []
            for img in images:
                url = img.get("url") or img.get("link") or img.get("href")
                if not url:
                    continue
                tags = img.get("tags", [])
                if any(t.get("label") == "floor_plan" for t in tags):
                    floor_plans.append({"url": url, "description": "floor_plan"})
                all_imgs.append({"url": url, "description": img.get("description", "")})

            return {"images": all_imgs, "floor_plans": floor_plans}
            
        except Exception as e:
            print(f"Error getting property photos: {e}")
            return {"images": [], "floor_plans": []}

    # Remove search_property method and all /search endpoint usage
    # Update get_property_id to skip API search and use only OpenAI and web scraping
    def extract_property_id_from_url(self, url: str) -> Optional[str]:
        """Extract property ID from a Realtor.com URL"""
        if not url:
            return None
        match = re.search(r'_M([\d-]+)', url)
        if match:
            numeric = match.group(1).replace('-', '')
            return numeric if numeric.isdigit() else None
        return None

    def get_property_id(self, address: str) -> Optional[str]:
        """High-level helper to get property ID via multiple strategies."""
        logger.info(f"Getting property ID for: {address}")
        
        # Strategy 1: Try SerpAPI if configured (most reliable)
        if self.serpapi_key:
            logger.info("Trying SerpAPI (Google Search)...")
            prop_id = self._get_property_id_serpapi(address)
            if prop_id:
                logger.info(f"SerpAPI returned property ID: {prop_id}")
                return prop_id
        
        # Strategy 2: Try web scraping if BeautifulSoup4 is available
        if HAS_BS4:
            logger.info("Trying web scraping methods...")
            
            # 2a: Try Realtor.com site search first (more reliable than DuckDuckGo)
            logger.info("Attempting Realtor.com site search...")
            realtor_url = self._realtor_site_search_url(address)
            if realtor_url:
                prop_id = self.extract_property_id_from_url(realtor_url)
                if prop_id:
                    logger.info(f"Realtor.com site search returned property ID: {prop_id}")
                    return prop_id
            
            # 2b: Try DuckDuckGo as fallback
            logger.info("Attempting DuckDuckGo search...")
            prop_id = self._scrape_property_id_duckduckgo(address)
            if prop_id:
                logger.info(f"DuckDuckGo returned property ID: {prop_id}")
                return prop_id
        else:
            logger.warning("BeautifulSoup4 not available, cannot perform web scraping")
        
        logger.warning("All property ID lookup methods failed")
        return None
    
    def _get_property_id_serpapi(self, address: str) -> Optional[str]:
        """Get property ID using SerpAPI (Google Search) - Most reliable method."""
        if not self.serpapi_key:
            return None
        
        try:
            # Remove unit numbers for base address
            # Handle patterns like: "#8C", "Apt 8C", ", #8C", ", Apt 8C"
            base_address = re.sub(r'\s*[,]?\s*[#]?\s*(apt|apartment|unit)\s*[a-zA-Z0-9/]+', '', address, flags=re.IGNORECASE)
            base_address = re.sub(r'\s*[,]?\s*#[a-zA-Z0-9/]+', '', base_address)
            base_address = base_address.strip().rstrip(',').strip()  # Clean up any trailing commas
            
            # Extract unit number from original address for validation
            unit_number = None
            unit_match = re.search(r'(?:apt|apartment|unit|#)\s*([a-zA-Z0-9/]+)', address, re.IGNORECASE)
            if unit_match:
                unit_number = unit_match.group(1).upper()
                logger.info(f"Extracted unit number for validation: {unit_number}")
            
            # Strategy: Try searching WITH the full address including unit first
            # This gives more precise results when the unit is listed
            search_queries = [
                f'"{address}" site:realtor.com/realestateandhomes-detail',  # Exact match with unit
                f"{address} site:realtor.com/realestateandhomes-detail",    # With unit, no quotes
                f"{base_address} site:realtor.com/realestateandhomes-detail"  # Without unit (fallback)
            ]
            
            for query in search_queries:
                params = {
                    "engine": "google",
                    "q": query,
                    "num": "10",  # Get more results to increase chances of finding correct one
                    "api_key": self.serpapi_key,
                }
                
                logger.info(f"SerpAPI query: {params['q']}")
                resp = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
                logger.info(f"SerpAPI status: {resp.status_code}")
                
                if resp.status_code != 200:
                    logger.warning(f"SerpAPI returned status {resp.status_code}")
                    continue
                
                data = resp.json()
                
                # Extract street number from requested address for validation
                addr_number_match = re.search(r'^(\d+)', base_address.strip())
                requested_street_num = addr_number_match.group(1) if addr_number_match else None
                
                # Extract street name from requested address for validation
                # e.g., "305 East 24th Street" -> "24"
                requested_street_name = None
                street_name_match = re.search(r'\d+\s+(?:east|west|north|south|e|w|n|s)\s+(\d+)(?:st|nd|rd|th)?', base_address, re.IGNORECASE)
                if street_name_match:
                    requested_street_name = street_name_match.group(1)  # e.g., "24"
                
                # Look through organic results for Realtor.com links
                for result in data.get("organic_results", []):
                    link = result.get("link", "")
                    if 'realtor.com/realestateandhomes-detail' in link:
                        logger.info(f"Found Realtor.com link: {link}")
                        
                        # Extract street number and name from URL for validation
                        # URL format: .../305-E-24th-St-Apt-8C_New-York_...
                        url_match = re.search(r'/(\d+)-(?:E|W|N|S|East|West|North|South)-(\d+)(?:st|nd|rd|th)?-', link, re.IGNORECASE)
                        if url_match:
                            url_street_num = url_match.group(1)  # e.g., "305"
                            url_street_name = url_match.group(2)  # e.g., "24"
                        else:
                            # Fallback: just extract street number
                            url_num_match = re.search(r'/(\d+)-', link)
                            url_street_num = url_num_match.group(1) if url_num_match else None
                            url_street_name = None
                        
                        # Validate street number matches
                        if requested_street_num and url_street_num:
                            if requested_street_num != url_street_num:
                                logger.warning(f"SerpAPI result rejected - street number mismatch: {requested_street_num} vs {url_street_num}")
                                logger.warning(f"Rejected URL: {link}")
                                continue  # Try next result
                        
                        # Validate street name matches (if we have both)
                        if requested_street_name and url_street_name:
                            if requested_street_name != url_street_name:
                                logger.warning(f"SerpAPI result rejected - street name mismatch: {requested_street_name} vs {url_street_name}")
                                logger.warning(f"Rejected URL: {link}")
                                continue  # Try next result
                        
                        # If we have a unit number, validate it matches the URL
                        if unit_number:
                            # Extract unit from URL: .../305-E-24th-St-Apt-8C_...
                            url_unit_match = re.search(r'-(?:Apt|Apartment|Unit)-([a-zA-Z0-9]+)(?:_|$)', link, re.IGNORECASE)
                            if url_unit_match:
                                url_unit = url_unit_match.group(1).upper()
                                if url_unit != unit_number:
                                    logger.warning(f"SerpAPI result rejected - unit mismatch: requested {unit_number}, got {url_unit}")
                                    logger.warning(f"Rejected URL: {link}")
                                    continue  # Try next result
                                else:
                                    logger.info(f"✓ Unit number validated: {unit_number} == {url_unit}")
                        
                        prop_id = self.extract_property_id_from_url(link)
                        if prop_id:
                            logger.info(f"SerpAPI validated and returning property ID: {prop_id}")
                            return prop_id
                
                logger.info(f"Query '{query}' found no valid property ID after validation")
            
            logger.warning("All SerpAPI queries failed to find valid property ID")
            return None
            
        except Exception as e:
            logger.error(f"Error in SerpAPI lookup: {e}")
            return None

    def _validate_address_match(self, requested_address: str, returned_address: str) -> bool:
        """Validate that the returned property address matches the requested address"""
        if not requested_address or not returned_address:
            return False
        
        # Normalize addresses for comparison
        req_lower = requested_address.lower().strip()
        ret_lower = returned_address.lower().strip()
        
        # Remove unit/apt info for comparison (including units with slashes like #10/11)
        # Handle patterns like: "#8C", "Apt 8C", ", #8C", ", Apt 8C"
        req_base = re.sub(r'\s*[,]?\s*[#]?\s*(apt|apartment|unit)\s*[a-zA-Z0-9/]+', '', req_lower, flags=re.IGNORECASE)
        ret_base = re.sub(r'\s*[,]?\s*[#]?\s*(apt|apartment|unit)\s*[a-zA-Z0-9/]+', '', ret_lower, flags=re.IGNORECASE)
        # Also remove standalone # patterns like "#10/11" or "#8C"
        req_base = re.sub(r'\s*[,]?\s*#[a-zA-Z0-9/]+', '', req_base)
        ret_base = re.sub(r'\s*[,]?\s*#[a-zA-Z0-9/]+', '', ret_base)
        # Clean up any trailing commas
        req_base = req_base.strip().rstrip(',').strip()
        ret_base = ret_base.strip().rstrip(',').strip()
        
        # Extract street number and name
        req_match = re.match(r'(\d+)\s+([a-z\s]+?)(?:street|st|avenue|ave|road|rd|place|pl|plaza)(?:\s|,|$)', req_base)
        ret_match = re.match(r'(\d+)\s+([a-z\s]+?)(?:street|st|avenue|ave|road|rd|place|pl|plaza)(?:\s|,|$)', ret_base)
        
        if not req_match or not ret_match:
            logger.warning(f"Could not parse addresses for validation: '{req_base}' vs '{ret_base}'")
            return False
        
        req_number = req_match.group(1)
        req_street = req_match.group(2).strip()
        ret_number = ret_match.group(1)
        ret_street = ret_match.group(2).strip()
        
        # Street numbers must match exactly
        if req_number != ret_number:
            logger.warning(f"Street number mismatch: requested {req_number}, got {ret_number}")
            return False
        
        # Street names must have significant overlap
        req_words = set(req_street.split())
        ret_words = set(ret_street.split())
        
        # Get significant words (length > 2, not common words)
        common_words = {'east', 'west', 'north', 'south', 'e', 'w', 'n', 's', 'st', 'ave', 'rd', 'pl'}
        req_significant = {w for w in req_words if len(w) > 2 and w not in common_words}
        ret_significant = {w for w in ret_words if len(w) > 2 and w not in common_words}
        
        # Check for overlap
        if req_significant and ret_significant:
            overlap = req_significant & ret_significant
            if not overlap:
                logger.warning(f"Street name mismatch: requested '{req_street}' ({req_significant}), got '{ret_street}' ({ret_significant})")
                return False
        
        logger.info(f"Address validation passed: '{requested_address}' matches '{returned_address}'")
        return True

    def get_all_property_data(self, address: str) -> Dict[str, Any]:
        """Get all property data in one call with optimized URL handling"""
        result = {
            "address": address,
            "property_details": None,
            "images": {"images": []},
            "floor_plans": {"floor_plans": []},
            "property_id": None,
            "realtor_url": None
        }

        # Get property ID first
        property_id = self.get_property_id(address)
        if property_id:
            result["property_id"] = property_id
            # Get property details
            time.sleep(1)  # Rate limiting
            details = self.get_property_details(property_id)
            if details:
                # CRITICAL: Validate that the returned property matches the requested address
                returned_address = details.get('address', '')
                if not self._validate_address_match(address, returned_address):
                    logger.error(f"Address mismatch! Requested: '{address}', Got: '{returned_address}'")
                    logger.error(f"Property ID {property_id} does not match the requested address. Discarding results.")
                    return result  # Return empty result
                
                result["property_details"] = details
                # Check if API response includes the URL
                if details.get('listing_url'):
                    result["realtor_url"] = details['listing_url']
                    logger.info(f"Got Realtor URL from API response: {details['listing_url']}")
            
            # Get photos and floor plans
            time.sleep(1)  # Rate limiting
            photos = self.get_property_photos(property_id)
            if photos:
                result["images"] = {"images": photos["images"]}
                result["floor_plans"] = {"floor_plans": photos["floor_plans"]}
            
            # If no URL from API, fall back to other methods
            if not result["realtor_url"]:
                logger.info("No URL from API, trying web scraping...")
                result["realtor_url"] = self.get_realtor_link(address)
                if not result["realtor_url"]:
                    # Last resort: construct URL
                    result["realtor_url"] = self.build_realtor_url(property_id, address)
                    logger.info(f"Constructed URL as fallback: {result['realtor_url']}")
        
        return result

    # NEW: Helper to format address for realtor slug
    def _slugify_address(self, address: str) -> Optional[str]:
        """Convert a full address to the slug format used by Realtor.com URLs."""
        try:
            logger.info(f"Slugifying address: {address}")
            parts = [p.strip() for p in address.split(',') if p.strip()]
            logger.info(f"Address parts: {parts}")
            if len(parts) < 3:
                logger.info(f"Not enough parts ({len(parts)}), need at least 3")
                return None  # Need at least street, city, state zip

            # Create Realtor-style street slug
            street_full = parts[0].strip()
            logger.info(f"Original street: {street_full}")
            
            # Remove apartment/unit info for the URL slug
            street_full = re.sub(r'\s*#\w+', '', street_full)  # Remove #8A, #4B, etc.
            street_full = re.sub(r'\s*,?\s*(apt|apartment|unit)\s*\w+', '', street_full, flags=re.IGNORECASE)
            logger.info(f"Street after removing unit: {street_full}")
            
            # Handle direction prefix
            dir_map = {"West": "W", "East": "E", "North": "N", "South": "S"}
            for word, abbr in dir_map.items():
                street_full = re.sub(rf"^{word} ", f"{abbr} ", street_full, flags=re.IGNORECASE)

            suffix_map = {
                "Street": "St",
                "Avenue": "Ave",
                "Place": "Pl",
                "Road": "Rd",
                "Court": "Ct",
                "Parkway": "Pkwy"
            }
            sf_parts = street_full.split()
            if sf_parts and sf_parts[-1].title() in suffix_map:
                sf_parts[-1] = suffix_map[sf_parts[-1].title()]
            street = '-'.join(sf_parts)
            logger.info(f"Final street slug: {street}")

            city_raw = parts[-2].lower().strip()
            # Normalize common NYC borough names that Realtor uses as "New-York"
            if city_raw in {"manhattan", "new york", "new york city"}:
                city = "New-York"
            else:
                city = parts[-2].replace(' ', '-')
            logger.info(f"City slug: {city}")
            
            state_zip = parts[-1].strip().split()
            if len(state_zip) < 1:
                logger.info(f"Invalid state_zip format: {parts[-1]}")
                return None
            
            state = state_zip[0]
            # Handle case where zip might be missing
            zip_code = state_zip[1] if len(state_zip) > 1 else ""
            
            if zip_code:
                slug = f"{street}_{city}_{state}_{zip_code}"
            else:
                slug = f"{street}_{city}_{state}"
            logger.info(f"Final slug: {slug}")
            return slug
        except Exception as e:
            logger.error(f"Error in _slugify_address: {e}")
            return None

    def build_realtor_url(self, property_id: str, address: str) -> Optional[str]:
        """Build a Realtor.com listing URL from property_id and address."""
        logger.info(f"Building Realtor URL for property_id: {property_id}, address: {address}")
        slug = self._slugify_address(address)
        logger.info(f"Generated slug: {slug}")
        if not slug or not property_id:
            logger.info(f"Cannot build URL - slug: {slug}, property_id: {property_id}")
            return None
        url = f"https://www.realtor.com/realestateandhomes-detail/{slug}_M{property_id}"
        logger.info(f"Built Realtor URL: {url}")
        return url

    def _extract_apartment_from_address(self, address: str) -> Optional[str]:
        """Extract apartment number from address string"""
        # Look for patterns like "Apt 8B", "Apartment 8B", "Unit 8B", "#8B"
        match = re.search(r'(?:apt|apartment|unit|#)\s*([a-zA-Z0-9]+)', address, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _extract_apartment_from_url(self, url: str) -> Optional[str]:
        """Extract apartment number from Realtor.com URL"""
        # Look for patterns like "Apt-8B" or "Apt-20H" in the URL
        match = re.search(r'Apt-([a-zA-Z0-9]+)', url, re.IGNORECASE)
        return match.group(1) if match else None

    def _scrape_property_id_duckduckgo(self, address: str) -> Optional[str]:
        """Search DuckDuckGo for the realtor listing and extract property ID."""
        try:
            import random
            import time
            
            # Extract key components for better matching
            # Remove unit/apt for base address
            # Handle patterns like: "#8C", "Apt 8C", ", #8C", ", Apt 8C"
            base_address = re.sub(r'\s*[,]?\s*[#]?\s*(apt|apartment|unit)\s*[a-zA-Z0-9/]+', '', address, flags=re.IGNORECASE)
            base_address = re.sub(r'\s*[,]?\s*#[a-zA-Z0-9/]+', '', base_address)
            base_address = base_address.strip().rstrip(',').strip()  # Clean up any trailing commas
            
            # Extract unit number from original address for validation
            unit_number = None
            unit_match = re.search(r'(?:apt|apartment|unit|#)\s*([a-zA-Z0-9/]+)', address, re.IGNORECASE)
            if unit_match:
                unit_number = unit_match.group(1).upper()
                logger.info(f"DuckDuckGo: Extracted unit number for validation: {unit_number}")
            
            # Try multiple search variations with increasing specificity
            search_queries = [
                f'"{address}" site:realtor.com/realestateandhomes-detail',  # With unit, exact match
                f"{address} site:realtor.com/realestateandhomes-detail",    # With unit
                f'"{base_address}" site:realtor.com/realestateandhomes-detail',  # Without unit, exact
                f"{base_address} site:realtor.com/realestateandhomes-detail",   # Without unit
            ]
            
            session = requests.Session()
            
            for query in search_queries:
                try:
                    # Enhanced headers to avoid bot detection
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate",  # Avoid br compression
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1"
                    }
                    
                    # Use the HTML interface for non-JavaScript access
                    encoded_query = urllib.parse.quote_plus(query)
                    url = f"https://duckduckgo.com/html/?q={encoded_query}"
                    
                    logger.info(f"DuckDuckGo search URL: {url}")
                    
                    # Add random delay to avoid rate limiting
                    time.sleep(random.uniform(1, 3))
                    
                    resp = session.get(url, headers=headers, timeout=15)
                    logger.info(f"DuckDuckGo response status: {resp.status_code}")
                    
                    if resp.status_code == 202:
                        logger.warning("DuckDuckGo returned status 202 - request accepted but not processed")
                        continue
                    elif resp.status_code != 200:
                        logger.warning(f"DuckDuckGo returned status {resp.status_code}")
                        continue
                    
                    # Check response length to ensure we got actual content
                    logger.info(f"DuckDuckGo response length: {len(resp.text)} chars")
                    if len(resp.text) < 5000:
                        logger.warning(f"DuckDuckGo returned short response ({len(resp.text)} chars)")
                        continue
                    
                    # Debug: Log response details
                    logger.info(f"DuckDuckGo HTML response received successfully")
                    
                    # Look for realtor.com URLs in the response text
                    # Extract both URL and surrounding text for validation
                    url_pattern = r'https://www\.realtor\.com/realestateandhomes-detail/([^"]*?)_M([\d-]+)'
                    matches = re.findall(url_pattern, resp.text)
                    
                    if matches:
                        logger.info(f"Found {len(matches)} potential property URLs in response")
                        
                        # Extract street name from requested address for validation
                        # e.g., "305 East 24th Street" -> "24"
                        requested_street_name = None
                        street_name_match = re.search(r'\d+\s+(?:east|west|north|south|e|w|n|s)\s+(\d+)(?:st|nd|rd|th)?', base_address, re.IGNORECASE)
                        if street_name_match:
                            requested_street_name = street_name_match.group(1)  # e.g., "24"
                        
                        # Validate each match against the original address
                        for url_slug, prop_id in matches:
                            clean_id = prop_id.replace('-', '')
                            if clean_id.isdigit() and len(clean_id) >= 8:
                                # Extract street name from URL slug for validation
                                # URL format: "305-E-24th-St-Apt-8C_New-York_NY_10002"
                                url_parts = url_slug.split('_')
                                if url_parts:
                                    url_street = url_parts[0].replace('-', ' ').lower()
                                    # Check if key address components match
                                    address_lower = base_address.lower()
                                    
                                    # Extract street name from address (first part before comma)
                                    addr_street = address_lower.split(',')[0].strip() if ',' in address_lower else address_lower
                                    
                                    # Extract street numbers for validation
                                    addr_number_match = re.search(r'^(\d+)', addr_street)
                                    url_number_match = re.search(r'^(\d+)', url_street)
                                    
                                    # Street numbers must match
                                    if addr_number_match and url_number_match:
                                        addr_number = addr_number_match.group(1)
                                        url_number = url_number_match.group(1)
                                        if addr_number != url_number:
                                            logger.warning(f"DuckDuckGo: Property ID {clean_id} rejected - street number mismatch: {addr_number} vs {url_number}")
                                            continue
                                    
                                    # Extract and validate street name (e.g., "24" from "24th")
                                    url_street_name = None
                                    url_street_name_match = re.search(r'(?:e|w|n|s|east|west|north|south)\s+(\d+)(?:st|nd|rd|th)?', url_street, re.IGNORECASE)
                                    if url_street_name_match:
                                        url_street_name = url_street_name_match.group(1)
                                    
                                    # Validate street name matches (if we have both)
                                    if requested_street_name and url_street_name:
                                        if requested_street_name != url_street_name:
                                            logger.warning(f"DuckDuckGo: Property ID {clean_id} rejected - street name mismatch: {requested_street_name} vs {url_street_name}")
                                            continue
                                    
                                    # If we have a unit number, validate it matches the URL
                                    if unit_number:
                                        # Extract unit from URL: .../305-E-24th-St-Apt-8C_...
                                        url_unit_match = re.search(r'-(?:Apt|Apartment|Unit)-([a-zA-Z0-9]+)(?:_|$)', url_slug, re.IGNORECASE)
                                        if url_unit_match:
                                            url_unit = url_unit_match.group(1).upper()
                                            if url_unit != unit_number:
                                                logger.warning(f"DuckDuckGo: Property ID {clean_id} rejected - unit mismatch: requested {unit_number}, got {url_unit}")
                                                continue  # Try next result
                                            else:
                                                logger.info(f"DuckDuckGo: ✓ Unit number validated: {unit_number} == {url_unit}")
                                    
                                    # Additional validation: check if main street name components are present
                                    # For "20 Confucius Plaza" we want to match "confucius"
                                    addr_words = set(addr_street.split())
                                    url_words = set(url_street.split())
                                    
                                    # Find significant words (not numbers, not common words)
                                    significant_addr_words = {w for w in addr_words if len(w) > 3 and not w.isdigit()}
                                    significant_url_words = {w for w in url_words if len(w) > 3 and not w.isdigit()}
                                    
                                    # Check if at least one significant word matches (or if we already validated street name)
                                    if (requested_street_name and url_street_name and requested_street_name == url_street_name) or (significant_addr_words & significant_url_words):
                                        logger.info(f"DuckDuckGo: Validated property ID {clean_id} - address match confirmed")
                                        logger.info(f"URL slug: {url_slug}")
                                        return clean_id
                                    else:
                                        logger.warning(f"DuckDuckGo: Property ID {clean_id} rejected - address mismatch")
                                        logger.warning(f"Expected words: {significant_addr_words}, URL words: {significant_url_words}")
                        
                        logger.warning("DuckDuckGo: Found property IDs but none matched the address validation")
                    
                    logger.info(f"Query '{query}' found no valid property IDs")
                    
                except Exception as e:
                    logger.error(f"Error with query '{query}': {e}")
                    continue
            
            logger.warning("All DuckDuckGo search queries failed to find property ID")
            return None
        except Exception as e:
            logger.error(f"Error in DuckDuckGo scraping: {e}")
            return None

    def get_realtor_link(self, address: str) -> Optional[str]:
        """Return canonical Realtor.com URL using cost-free layered strategy."""
        logger.info(f"Getting Realtor link for: {address}")
        
        if not HAS_BS4:
            logger.warning("BeautifulSoup4 not available, skipping web scraping methods")
            # Skip directly to property ID construction
            pid = self.get_property_id(address)
            logger.info(f"get_property_id returned: {pid}")
            if pid:
                constructed_url = self.build_realtor_url(pid, address)
                logger.info(f"build_realtor_url constructed: {constructed_url}")
                return constructed_url
            logger.info("No Realtor.com URL found for address.")
            return None
        
        # 1. Try direct site search (free)
        url = self._realtor_site_search_url(address)
        logger.info(f"_realtor_site_search_url returned: {url}")
        if url:
            return url
        # 2. DuckDuckGo fallback
        url = self._scrape_realtor_url_duckduckgo(address)
        logger.info(f"_scrape_realtor_url_duckduckgo returned: {url}")
        if url:
            return url
        # 3. If SerpAPI key configured, use it
        url = self._serpapi_realtor_url(address)
        logger.info(f"_serpapi_realtor_url returned: {url}")
        if url:
            return url
        # 4. As last resort construct from ID (may be inaccurate slug)
        pid = self.get_property_id(address)
        logger.info(f"get_property_id returned: {pid}")
        if pid:
            constructed_url = self.build_realtor_url(pid, address)
            logger.info(f"build_realtor_url constructed: {constructed_url}")
            return constructed_url
        logger.info("No Realtor.com URL found for address.")
        return None

    def _remove_unit_part(self, address: str) -> str:
        """Remove unit/apartment part from address for better matching."""
        # Remove common unit patterns
        patterns = [
            r',?\s*(apt|apartment|unit|#)\s*[a-zA-Z0-9]+',  # Apt 4, Unit 5, #3A
            r',?\s*#\s*[a-zA-Z0-9]+',  # #4B
            r',?\s*[a-zA-Z0-9]+\s*$'  # Any trailing alphanumeric that might be a unit
        ]
        result = address
        for pattern in patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        return result.strip()

    def _realtor_site_search_url(self, address: str) -> Optional[str]:
        """Query Realtor.com's own search page and return first result URL."""
        try:
            address_no_unit = self._remove_unit_part(address)
            slug = self._slugify_address(address_no_unit)
            print(f"[DEBUG] _realtor_site_search_url: slugified address: {slug}")
            if not slug:
                return None
            search_url = f"https://www.realtor.com/realestateandhomes-search/{slug}"
            print(f"[DEBUG] _realtor_site_search_url: search_url: {search_url}")
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

            # Retry up to 3 times with small back-off when Realtor blocks (429) or temporary error
            for attempt in range(3):
                resp = requests.get(search_url, headers=headers, timeout=10)
                print(f"[DEBUG] _realtor_site_search_url: Attempt {attempt+1}, status: {resp.status_code}")
                if resp.status_code == 200:
                    break
                if resp.status_code in {429, 403, 502} and attempt < 2:
                    time.sleep(2 + attempt)  # incremental back-off
                    continue
                return None
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.select('a'):  # look for anchor tags with detail links
                href = a.get('href', '')
                if '/realestateandhomes-detail/' in href:
                    if href.startswith('http'):
                        print(f"[DEBUG] _realtor_site_search_url: Found detail link: {href}")
                        return href
                    else:
                        full_url = 'https://www.realtor.com' + href
                        print(f"[DEBUG] _realtor_site_search_url: Found detail link: {full_url}")
                        return full_url
            print("[DEBUG] _realtor_site_search_url: No detail link found on search page.")
            return None
        except Exception as e:
            print(f"[DEBUG] _realtor_site_search_url: Exception: {e}")
            return None

    def _scrape_realtor_url_duckduckgo(self, address: str) -> Optional[str]:
        """Search DuckDuckGo for the Realtor.com listing and return its URL. Try address variations."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            tried = set()
            variations = [address]
            # Try without unit/apt
            stripped = self._remove_unit_part(address)
            if stripped != address:
                variations.append(stripped)
            # Try with direction abbreviation expanded/collapsed
            dir_map = {" N ": [" North ", " N "], " S ": [" South ", " S "], " E ": [" East ", " E "], " W ": [" West ", " W "]}
            for v in list(variations):
                for k, vals in dir_map.items():
                    for val in vals:
                        if val in v:
                            # Try both expanded and abbreviated
                            variations.append(v.replace(val, k.strip() + ' '))
                            variations.append(v.replace(val, val[0] + ' '))
            # Remove duplicates
            variations = list(dict.fromkeys(variations))
            print(f"[DEBUG] _scrape_realtor_url_duckduckgo: Trying variations: {variations}")
            for v in variations:
                if not v or v in tried:
                    continue
                tried.add(v)
                query = urllib.parse.quote_plus(f"{v} site:realtor.com/realestateandhomes-detail")
                url = f"https://duckduckgo.com/html/?q={query}"
                print(f"[DEBUG] _scrape_realtor_url_duckduckgo: Searching DuckDuckGo with URL: {url}")
                resp = requests.get(url, headers=headers, timeout=10)
                print(f"[DEBUG] _scrape_realtor_url_duckduckgo: DuckDuckGo status: {resp.status_code}")
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.select('a.result__a'):
                    href = a.get('href', '')
                    if 'uddg=' in href:
                        real_url = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get('uddg', [None])[0]
                    else:
                        real_url = href
                    print(f"[DEBUG] _scrape_realtor_url_duckduckgo: Found link: {real_url}")
                    if real_url and 'realtor.com/realestateandhomes-detail' in real_url:
                        print(f"[DEBUG] _scrape_realtor_url_duckduckgo: Returning detail link: {real_url}")
                        return real_url
            print("[DEBUG] _scrape_realtor_url_duckduckgo: No detail link found in DuckDuckGo results.")
            return None
        except Exception as e:
            print(f"[DEBUG] _scrape_realtor_url_duckduckgo: Exception: {e}")
            return None

    # NEW: SerpAPI search
    def _serpapi_realtor_url(self, address: str) -> Optional[str]:
        if not self.serpapi_key:
            return None
        try:
            params = {
                "engine": "google",
                "q": f"{address} site:realtor.com/realestateandhomes-detail",
                "num": "10",
                "api_key": self.serpapi_key,
            }
            print(f"[DEBUG] _serpapi_realtor_url: Query params: {params}")
            resp = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
            print(f"[DEBUG] _serpapi_realtor_url: SerpAPI status: {resp.status_code}")
            if resp.status_code != 200:
                return None
            data = resp.json()
            for res in data.get("organic_results", []):
                link = res.get("link")
                print(f"[DEBUG] _serpapi_realtor_url: Found link: {link}")
                if link and 'realtor.com/realestateandhomes-detail' in link:
                    print(f"[DEBUG] _serpapi_realtor_url: Returning detail link: {link}")
                    return link
            print("[DEBUG] _serpapi_realtor_url: No detail link found in SerpAPI results.")
            return None
        except Exception as e:
            print(f"[DEBUG] _serpapi_realtor_url: Exception: {e}")
            return None
