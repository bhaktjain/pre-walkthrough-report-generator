# Unit Number Validation Fix - Preventing Wrong Unit Returns

## Issue Summary

**Problem**: System was returning the wrong unit when looking up "305 East 24th Street #8C"
- **Requested**: 305 East 24th Street #8C (Apt 8C)
- **Returned**: 305 E 24th St Apt Le (Property ID: 3240017896)
- **Expected**: 305 E 24th St Apt 8C (Property ID: 3658693240)

## Root Cause

When searching without the unit number (e.g., "305 East 24th Street"), Google/SerpAPI returns ANY unit in that building. The system was accepting the first result without validating that the unit number matched the requested unit.

**Example**:
- Search: "305 East 24th Street site:realtor.com"
- Google returns: Multiple units (Apt Le, Apt 8C, Apt 5A, etc.)
- System took: First result (Apt Le) ❌
- Should take: Only Apt 8C ✓

## Solution Implemented

### 1. Extract Unit Number from Requested Address

Added logic to extract and store the unit number for validation:

```python
# Extract unit number from original address for validation
unit_number = None
unit_match = re.search(r'(?:apt|apartment|unit|#)\s*([a-zA-Z0-9/]+)', address, re.IGNORECASE)
if unit_match:
    unit_number = unit_match.group(1).upper()
    logger.info(f"Extracted unit number for validation: {unit_number}")
```

**Handles all formats**:
- `#8C` → `8C`
- `Apt 8C` → `8C`
- `Apartment 8C` → `8C`
- `Unit 8C` → `8C`

### 2. Multi-Query Search Strategy

Changed from single query to multiple queries with fallback:

```python
search_queries = [
    f'"{address}" site:realtor.com/realestateandhomes-detail',  # Exact match with unit
    f"{address} site:realtor.com/realestateandhomes-detail",    # With unit, no quotes
    f"{base_address} site:realtor.com/realestateandhomes-detail"  # Without unit (fallback)
]
```

**Benefits**:
1. Try exact match first (most precise)
2. Try with unit but no quotes (more flexible)
3. Fall back to without unit only if needed

### 3. Unit Number Validation

Added validation to check that the returned property's unit matches the requested unit:

```python
# If we have a unit number, validate it matches the URL
if unit_number:
    # Extract unit from URL: .../305-E-24th-St-Apt-8C_...
    url_unit_match = re.search(r'-(?:Apt|Apartment|Unit)-([a-zA-Z0-9]+)(?:_|$)', link, re.IGNORECASE)
    if url_unit_match:
        url_unit = url_unit_match.group(1).upper()
        if url_unit != unit_number:
            logger.warning(f"Result rejected - unit mismatch: requested {unit_number}, got {url_unit}")
            continue  # Try next result
        else:
            logger.info(f"✓ Unit number validated: {unit_number} == {url_unit}")
```

**Validation Flow**:
1. Extract unit from URL (e.g., "Apt-8C" → "8C")
2. Compare with requested unit
3. Reject if mismatch
4. Accept only if exact match

### 4. Applied to Both SerpAPI and DuckDuckGo

The unit validation logic was added to both search methods:
- `_get_property_id_serpapi()` - Primary method using SerpAPI
- `_scrape_property_id_duckduckgo()` - Fallback method using DuckDuckGo

## Testing

Created comprehensive test suite (`test_unit_validation.py`) with 4 test categories:

### Test 1: Regex Pattern Validation
Tests that unit numbers are correctly removed from addresses:
- ✓ `305 East 24th Street #8C, New York, NY` → `305 East 24th Street, New York, NY`
- ✓ `305 East 24th Street, Apt 8C, New York, NY` → `305 East 24th Street, New York, NY`
- ✓ All 5 format variations pass

### Test 2: Unit Number Extraction
Tests that unit numbers are correctly extracted:
- ✓ `#8C` → `8C`
- ✓ `Apt 8C` → `8C`
- ✓ `Unit 8C` → `8C`
- ✓ No unit → `None`

### Test 3: URL Unit Extraction
Tests that unit numbers are correctly extracted from URLs:
- ✓ `.../305-E-24th-St-Apt-8C_...` → `8C`
- ✓ `.../305-E-24th-St-Apartment-8C_...` → `8C`
- ✓ `.../305-E-24th-St-Unit-8C_...` → `8C`
- ✓ No unit in URL → `None`

### Test 4: Live Property Lookup
Tests actual property lookup with SerpAPI:
- ✓ Returns correct property ID: `3658693240` (Apt 8C)
- ✓ Does NOT return wrong property ID: `3240017896` (Apt Le)

**All tests passed before commit!**

## Files Modified

1. **pre_walkthrough_generator/src/property_api.py**
   - Modified `_get_property_id_serpapi()`:
     - Added unit number extraction
     - Changed to multi-query search strategy
     - Added unit validation logic
   - Modified `_scrape_property_id_duckduckgo()`:
     - Added unit number extraction
     - Changed to multi-query search strategy
     - Added unit validation logic

2. **test_unit_validation.py** (new file)
   - Comprehensive test suite
   - 4 test categories
   - All tests passing

## Validation Logic Summary

The system now validates THREE components:
1. **Street Number**: "305" must match "305"
2. **Street Name**: "24" must match "24" (from "24th")
3. **Unit Number**: "8C" must match "8C" (NEW!)

**Example Validation**:
```
Requested: 305 East 24th Street #8C
URL: .../305-E-24th-St-Apt-8C_New-York_...

✓ Street number: 305 == 305
✓ Street name: 24 == 24
✓ Unit number: 8C == 8C
→ ACCEPT
```

```
Requested: 305 East 24th Street #8C
URL: .../305-E-24th-St-Apt-Le_New-York_...

✓ Street number: 305 == 305
✓ Street name: 24 == 24
✗ Unit number: 8C != Le
→ REJECT
```

## Impact

This fix ensures that:
1. Users get the correct unit when searching with unit numbers
2. System doesn't return random units from the same building
3. Property data matches the exact unit requested
4. Validation is comprehensive (street number + street name + unit)
5. Search strategy is optimized (try with unit first, fall back if needed)

## Related Fixes

This is the third fix in the property lookup improvement series:
1. **ADDRESS_VALIDATION_FIX.md** - Added address validation after property details retrieval
2. **PROPERTY_LOOKUP_BUG_FIX.md** - Fixed regex patterns and added street name validation
3. **UNIT_VALIDATION_FIX.md** (this fix) - Added unit number validation

Together, these fixes ensure accurate property lookups with comprehensive validation.
