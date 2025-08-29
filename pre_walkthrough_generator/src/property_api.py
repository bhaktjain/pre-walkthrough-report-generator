import requests
import re
from typing import Dict, Any, Optional
import time
import http.client
import json
from openai import OpenAI
import urllib.parse
from bs4 import BeautifulSoup
import logging

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
        """Use OpenAI to get the property ID or MLS ID"""
        try:
            if not self.openai_api_key:
                return None

            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that finds property listings and their IDs. You have access to web search and MLS databases. When searching, look for any type of listing ID (MLS #, Listing #, etc) and return it exactly as found."},
                    {"role": "user", "content": address}
                ],
                temperature=0,
                max_tokens=100
            )
            
            raw = response.choices[0].message.content.strip()
            if raw.lower() == 'none':
                return None
                
            # Capture IDs that may contain a hyphen (e.g., M48195-62808)
            match = re.search(r'[mM]([\d-]{9,15})', raw)
            if not match:
                return None
            numeric = match.group(1).replace('-', '')  # strip hyphen
            return numeric if numeric.isdigit() else None
            
        except Exception as e:
            print(f"Error getting listing ID from OpenAI: {e}")
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
                for det in d.get('details', []):
                    if category and det.get('category', '').lower() == category.lower():
                        for t in det.get('text', []):
                            if regex:
                                m = re.search(regex, t)
                                if m:
                                    return m.group(1)
                            elif contains and contains.lower() in t.lower():
                                return t
                            else:
                                return t
                    for t in det.get('text', []):
                        if contains and contains.lower() in t.lower():
                            return t
                        if regex:
                            m = re.search(regex, t)
                            if m:
                                return m.group(1)
                return None

            def search_details_any(regex):
                for det in d.get('details', []):
                    for t in det.get('text', []):
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
            bedrooms = d.get('description', {}).get('beds')
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
            bathrooms = d.get('description', {}).get('baths') or d.get('description', {}).get('baths_consolidated')
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
            sqft = d.get('description', {}).get('sqft')
            if not sqft:
                sqft = search_details_any(r'(\d{3,5})\s*sqft')
            if not sqft:
                # Try property_history
                for hist in d.get('property_history', []):
                    listing = hist.get('listing') or {}
                    desc = listing.get('description', {}) if listing else {}
                    if desc and desc.get('sqft'):
                        sqft = desc['sqft']
                        break
            if not sqft:
                sqft = 'Information not available'
            print(f"[DEBUG] Sqft: {sqft}")

            # Year Built
            year_built = d.get('description', {}).get('year_built')
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
            property_type = d.get('description', {}).get('type') or d.get('description', {}).get('sub_type')
            if not property_type:
                property_type = search_details_any(r'Property Subtype: ([\w-]+)')
            if not property_type:
                for det in d.get('details', []):
                    for t in det.get('text', []):
                        if 'property subtype' in t.lower():
                            property_type = t.split(':')[-1].strip()
                            break
            if not property_type:
                property_type = 'Information not available'
            print(f"[DEBUG] Property Type: {property_type}")

            # Neighborhood
            neighborhood = None
            neighborhoods = d.get('location', {}).get('neighborhoods', [])
            if neighborhoods:
                neighborhood = neighborhoods[0].get('name')
            if not neighborhood:
                neighborhood = search_details_any(r'Neighborhood: ([\w\s-]+)')
            if not neighborhood:
                for det in d.get('details', []):
                    for t in det.get('text', []):
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
                for photo in d.get('photos', []):
                    if not photo:
                        continue
                    href = photo.get('href')
                    if not href:
                        continue
                    tags = [tag.get('label', '') for tag in (photo.get('tags', []) or []) if tag and tag.get('label')]
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
        """High-level helper to get property ID via OpenAI -> Web scrape."""
        logger.info(f"Getting property ID for: {address}")
        # 1. OpenAI
        pid = self.get_property_id_from_openai(address)
        if pid and pid.isdigit():
            logger.info(f"OpenAI returned property ID: {pid}")
            return pid
        # 2. Web scrape fallback
        pid = self._scrape_property_id_duckduckgo(address)
        logger.info(f"Web scrape returned property ID: {pid}")
        return pid

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
            
            state_zip = parts[-1].split()
            if len(state_zip) < 2:
                logger.info(f"Invalid state_zip format: {parts[-1]}")
                return None
            state = state_zip[0]
            zip_code = state_zip[1]
            
            slug = f"{street}_{city}_{state}_{zip_code}"
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
            query = urllib.parse.quote_plus(f"{address} site:realtor.com")
            url = f"https://duckduckgo.com/html/?q={query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.select('a.result__a'):
                href = a.get('href', '')
                # DuckDuckGo wraps links: /l/?uddg=<URL-ENCODED>
                if 'uddg=' in href:
                    real_url = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get('uddg', [None])[0]
                else:
                    real_url = href
                if real_url and 'realtor.com/realestateandhomes-detail' in real_url:
                    # Check if the URL contains the specific apartment number from the search
                    original_apt = self._extract_apartment_from_address(address)
                    if original_apt:
                        url_apt = self._extract_apartment_from_url(real_url)
                        if url_apt and url_apt.lower() != original_apt.lower():
                            print(f"[DEBUG] Apartment mismatch: searched for {original_apt}, found {url_apt}")
                            continue  # Skip this result, look for exact apartment match
                    
                    match = re.search(r'_M([\d-]+)', real_url)
                    if match:
                        numeric = match.group(1).replace('-', '')
                        return numeric if numeric.isdigit() else None
            return None
        except Exception:
            return None

    def get_realtor_link(self, address: str) -> Optional[str]:
        """Return canonical Realtor.com URL using cost-free layered strategy."""
        logger.info(f"Getting Realtor link for: {address}")
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
