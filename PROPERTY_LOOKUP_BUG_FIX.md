# Property Lookup Bug Fix - Wrong Property Returned

## Issue Summary

**Problem**: System was returning wrong property data when looking up "305 East 24th Street #8C"
- **Requested**: 305 East 24th Street #8C, New York, NY 10010
- **Returned**: 440 E 23rd St Apt 8C (Property ID: 3091414216)
- **Expected**: 305 E 24th St Apt 8C (Property ID: 3658693240)

## Root Cause Analysis

### Bug #1: Search Query Using Full Address with Unit Number
**Location**: `pre_walkthrough_generator/src/property_api.py` - `_get_property_id_serpapi()` method

**Problem**: The code was removing unit numbers for validation purposes but then searching with the FULL address including the unit:

```python
# Remove unit numbers for better search results
base_address = re.sub(r'\s*[#,]?\s*(apt|apartment|unit)\s*[a-zA-Z0-9/]+', '', address, flags=re.IGNORECASE)
base_address = re.sub(r'\s*#[a-zA-Z0-9/]+', '', base_address)

# BUG: Using original 'address' instead of 'base_address'
params = {
    "engine": "google",
    "q": f"{address} site:realtor.com/realestateandhomes-detail",  # ❌ WRONG
    "num": "10",
    "api_key": self.serpapi_key,
}
```

**Impact**: Searching with the full unit number (e.g., "#8C") could cause Google to return wrong results if:
- The exact unit doesn't exist or is off-market
- There are similar units in nearby buildings
- Google's algorithm prioritizes other similar listings

### Bug #2: Insufficient Validation - Only Street Number Checked
**Location**: `pre_walkthrough_generator/src/property_api.py` - `_get_property_id_serpapi()` method

**Problem**: The validation was only checking the street NUMBER (e.g., "305") but not the street NAME (e.g., "24th"):

```python
# Only validated street number
url_match = re.search(r'/(\d+)-', link)
url_street_num = url_match.group(1) if url_match else None

if requested_street_num != url_street_num:
    continue  # Reject
```

**Impact**: This would allow mismatches like:
- ✓ "305 East 24th Street" vs "305 East 25th Street" (WRONG - different streets!)
- ✓ "305 East 24th Street" vs "305 West 24th Street" (WRONG - different sides!)

## Solution Implemented

### Fix #1: Use Base Address (Without Unit) in Search Query
Changed the SerpAPI search to use `base_address` instead of `address`:

```python
# Search Google for the property on Realtor.com (use base_address without unit)
params = {
    "engine": "google",
    "q": f"{base_address} site:realtor.com/realestateandhomes-detail",  # ✅ CORRECT
    "num": "10",
    "api_key": self.serpapi_key,
}
```

**Benefit**: Searching without the unit number gives more reliable results and avoids confusion when the exact unit isn't listed.

### Fix #2: Enhanced Validation - Check Both Street Number AND Street Name
Added street name validation to both SerpAPI and DuckDuckGo methods:

```python
# Extract street name from requested address
# e.g., "305 East 24th Street" -> "24"
requested_street_name = None
street_name_match = re.search(r'\d+\s+(?:east|west|north|south|e|w|n|s)\s+(\d+)(?:st|nd|rd|th)?', base_address, re.IGNORECASE)
if street_name_match:
    requested_street_name = street_name_match.group(1)

# Extract street number and name from URL
# URL format: .../305-E-24th-St-Apt-8C_New-York_...
url_match = re.search(r'/(\d+)-(?:E|W|N|S|East|West|North|South)-(\d+)(?:st|nd|rd|th)?-', link, re.IGNORECASE)
if url_match:
    url_street_num = url_match.group(1)   # e.g., "305"
    url_street_name = url_match.group(2)  # e.g., "24"

# Validate BOTH street number and street name
if requested_street_num != url_street_num:
    logger.warning(f"Street number mismatch: {requested_street_num} vs {url_street_num}")
    continue  # Reject

if requested_street_name and url_street_name:
    if requested_street_name != url_street_name:
        logger.warning(f"Street name mismatch: {requested_street_name} vs {url_street_name}")
        continue  # Reject
```

**Benefit**: Now the system validates:
1. Street number matches (e.g., "305" == "305")
2. Street name matches (e.g., "24" == "24")
3. This prevents returning properties from different streets or different sides

## Files Modified

1. **pre_walkthrough_generator/src/property_api.py**
   - Fixed `_get_property_id_serpapi()` method:
     - Changed search query to use `base_address` instead of `address`
     - Added street name extraction and validation
     - Enhanced URL parsing to extract both street number and name
   - Fixed `_scrape_property_id_duckduckgo()` method:
     - Added street name extraction and validation
     - Enhanced validation logic to check street name in addition to street number

## Testing

To test the fix:

```bash
python3 test_address_issue.py
```

Expected results:
- Property ID should be: 3658693240
- Address should be: 305 E 24th St Apt 8C
- Validation should PASS

## Impact

This fix ensures that:
1. Property lookups are more accurate by searching without unit numbers
2. Wrong properties are rejected through enhanced validation
3. Users get the correct property data for their requested address
4. The system is more robust against similar addresses in nearby buildings

## Related Issues

- Previous fix: ADDRESS_VALIDATION_FIX.md (added `_validate_address_match()` method)
- This fix complements the previous one by preventing wrong property IDs from being found in the first place
