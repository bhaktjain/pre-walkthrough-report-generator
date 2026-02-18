# Property Lookup Fix - Address Mismatch Issue

## Issue Summary
**Date**: Current  
**Problem**: System returned wrong property (20 Waterside Plaza instead of 20 Confucius Plaza)  
**Severity**: High - Incorrect property data in reports

---

## What Happened

### Input:
```
Address: 20 Confucius Plaza #13A, New York, NY 10002
```

### Output (WRONG):
```
Property: 20 Waterside Plz Apt 13A, New York, NY 10010
Property ID: 3421174244
Neighborhood: Kips Bay (should be Chinatown)
```

### Why It's Wrong:
- **Confucius Plaza** is in Chinatown (10002)
- **Waterside Plaza** is in Kips Bay (10010)
- Different buildings, different neighborhoods, ~1 mile apart

---

## Root Cause Analysis

### 1. SerpAPI Failed ❌
```
INFO:property_api:No property ID found in SerpAPI results
```
- Most reliable method but returned no results
- Possible reasons: Property not indexed, search query too specific

### 2. Realtor.com Site Search Failed ❌
```
INFO:property_api:Invalid state_zip format: NY
```
- Address parsing bug in `_slugify_address()` function
- Expected format: "NY 10002"
- Received: "NY" (zip code missing from parsed parts)
- Code at line 621-623 required exactly 2 parts in state_zip

### 3. DuckDuckGo Matched Wrong Property ❌
```
INFO:property_api:Found Realtor.com URL: https://www.realtor.com/realestateandhomes-detail/20-Waterside-Plz-Apt-13A_New-York_NY_10010_M34211-74244
```

**Why DuckDuckGo Failed:**
- Search query was too broad after cleaning: `20 Confucius Plaza  13A New York NY 10002 site:realtor.com`
- DuckDuckGo's fuzzy matching algorithm matched on:
  - Street number: `20` ✓
  - Unit number: `13A` ✓
  - City: `New York` ✓
- But ignored the actual street name difference:
  - **Confucius Plaza** ≠ **Waterside Plaza**
- No validation of street name match
- Returned first result without verification

---

## The Fix

### Changes Made:

#### 1. Improved DuckDuckGo Search Strategy
**File**: `pre_walkthrough_generator/src/property_api.py`

**Before:**
```python
# Clean address for better search
clean_address = address.replace("#", " ").replace(",", "")

search_queries = [
    f"{clean_address} site:realtor.com",
    f'"{clean_address}" site:realtor.com',
    # ...
]
```

**After:**
```python
# Remove unit/apt for initial search to avoid confusion
base_address = re.sub(r'\s*[#,]?\s*(apt|apartment|unit)\s*[a-zA-Z0-9]+', '', address, flags=re.IGNORECASE)
base_address = re.sub(r'\s*#[a-zA-Z0-9]+', '', base_address)

# Try multiple search variations with increasing specificity
search_queries = [
    f'"{base_address}" site:realtor.com/realestateandhomes-detail',  # Most specific first
    f"{base_address} site:realtor.com/realestateandhomes-detail",
    # ...
]
```

**Benefits:**
- Removes unit numbers that can cause confusion
- Uses quoted search for exact phrase matching
- Searches specific detail pages only

#### 2. Added Address Validation
**File**: `pre_walkthrough_generator/src/property_api.py`

**Before:**
```python
# Just extract property ID without validation
realtor_urls = re.findall(r'https://www\.realtor\.com/realestateandhomes-detail/[^"]*_M([\d-]+)', resp.text)
for prop_id in realtor_urls:
    clean_id = prop_id.replace('-', '')
    if clean_id.isdigit() and len(clean_id) >= 8:
        return clean_id  # Return first match
```

**After:**
```python
# Extract URL slug AND property ID for validation
url_pattern = r'https://www\.realtor\.com/realestateandhomes-detail/([^"]*?)_M([\d-]+)'
matches = re.findall(url_pattern, resp.text)

for url_slug, prop_id in matches:
    # Extract street name from URL: "20-Confucius-Plaza_New-York_NY_10002"
    url_parts = url_slug.split('_')
    url_street = url_parts[0].replace('-', ' ').lower()
    
    # Extract street name from original address
    addr_street = address_lower.split(',')[0].strip()
    
    # Find significant words (not numbers, not common words)
    significant_addr_words = {w for w in addr_street.split() if len(w) > 3 and not w.isdigit()}
    significant_url_words = {w for w in url_street.split() if len(w) > 3 and not w.isdigit()}
    
    # Validate: at least one significant word must match
    if significant_addr_words & significant_url_words:
        return clean_id  # Validated match
    else:
        logger.warning(f"Property ID {clean_id} rejected - address mismatch")
```

**Benefits:**
- Validates street name before accepting property ID
- Compares significant words (e.g., "Confucius" vs "Waterside")
- Rejects false matches
- Logs mismatches for debugging

#### 3. Fixed Address Parsing Bug
**File**: `pre_walkthrough_generator/src/property_api.py`

**Before:**
```python
state_zip = parts[-1].split()
if len(state_zip) < 2:
    logger.info(f"Invalid state_zip format: {parts[-1]}")
    return None  # Fail if zip missing
state = state_zip[0]
zip_code = state_zip[1]
```

**After:**
```python
state_zip = parts[-1].strip().split()
if len(state_zip) < 1:
    logger.info(f"Invalid state_zip format: {parts[-1]}")
    return None

state = state_zip[0]
zip_code = state_zip[1] if len(state_zip) > 1 else ""

if zip_code:
    slug = f"{street}_{city}_{state}_{zip_code}"
else:
    slug = f"{street}_{city}_{state}"  # Handle missing zip
```

**Benefits:**
- Handles addresses with missing zip codes
- More flexible parsing
- Prevents unnecessary failures

---

## Testing

### Test Case 1: Original Failing Address
```python
address = "20 Confucius Plaza #13A, New York, NY 10002"
```

**Expected Result:**
- Should find correct property ID for Confucius Plaza
- Should reject Waterside Plaza (3421174244)
- Should validate street name match

### Test Case 2: Similar Addresses
```python
addresses = [
    "20 Confucius Plaza, New York, NY 10002",
    "20 Waterside Plaza, New York, NY 10010",
    "135 East 18th Street, New York, NY 10003"
]
```

**Expected Result:**
- Each should return correct property
- No cross-contamination between similar addresses

---

## Prevention Measures

### 1. Always Validate Street Names
- Don't rely solely on street number + unit
- Compare significant words in street names
- Log validation failures for review

### 2. Use Specific Search Queries
- Include full path: `site:realtor.com/realestateandhomes-detail`
- Use quoted searches for exact phrases
- Remove confusing elements (unit numbers)

### 3. Improve SerpAPI Reliability
- Review why SerpAPI failed
- Consider adjusting search query format
- Add retry logic with query variations

### 4. Add Manual Override
- Allow users to provide property ID directly
- Add property ID validation endpoint
- Implement property ID cache for known addresses

---

## Monitoring

### Metrics to Track:
1. **Property ID Match Rate**: % of successful lookups
2. **Validation Rejection Rate**: % of IDs rejected by validation
3. **Method Success Rate**: Which method (SerpAPI, Realtor, DuckDuckGo) works best
4. **Address Mismatch Alerts**: Log when validation rejects a match

### Logging Improvements:
```python
logger.info(f"Search query: {query}")
logger.info(f"Found {len(matches)} potential matches")
logger.info(f"Validated: {validated_count}, Rejected: {rejected_count}")
logger.warning(f"Address mismatch: Expected '{expected}', Got '{actual}'")
```

---

## Deployment

### Files Modified:
- `pre_walkthrough_generator/src/property_api.py`

### Testing Required:
1. Unit tests for address validation
2. Integration tests with real addresses
3. Regression tests for previously working addresses

### Rollback Plan:
- Git commit hash: [to be added]
- Backup of original file available
- Can revert via: `git revert <commit>`

---

## Summary

**Problem**: DuckDuckGo returned wrong property due to fuzzy matching on partial address components.

**Solution**: 
1. Improved search queries (remove units, use quotes)
2. Added street name validation before accepting property ID
3. Fixed address parsing to handle missing zip codes

**Impact**: 
- Prevents incorrect property data in reports
- Improves accuracy of property lookups
- Better error logging for debugging

**Status**: ✅ Fixed and ready for testing

---

**Created**: [Current Date]  
**Author**: Kiro AI Assistant  
**Priority**: High  
**Category**: Bug Fix
