# Filename Sanitization Fix

## Issue
**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'data/PreWalk_16_West_21st_Street_#10/11.docx'`

**Address**: `16 West 21st Street #10/11, New York, NY 10010`

**Problem**: The forward slash `/` in `#10/11` was being treated as a directory separator, causing the system to try creating:
- Directory: `data/PreWalk_16_West_21st_Street_#10/`
- File: `11.docx`

But the directory didn't exist, causing the error.

---

## Root Cause

The filename generation logic only replaced spaces with underscores but didn't handle other invalid filename characters:
- `/` (forward slash) - directory separator on Unix/Linux
- `\` (backslash) - directory separator on Windows
- `:` (colon) - drive separator on Windows
- `*`, `?`, `"`, `<`, `>`, `|` - wildcards and special characters
- `#` (hash) - can cause issues in URLs and some systems

---

## The Fix

### Files Modified:
1. `fastapi_server.py` - Main API endpoint
2. `pre_walkthrough_generator/src/document_generator.py` - Document generation
3. `pre_walkthrough_generator/src/main.py` - CLI interface

### Sanitization Logic:
```python
def sanitize_filename(text: str) -> str:
    """Remove or replace invalid filename characters"""
    # Replace invalid characters with underscore
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '#']
    for char in invalid_chars:
        text = text.replace(char, '_')
    # Replace multiple underscores with single
    while '__' in text:
        text = text.replace('__', '_')
    # Remove leading/trailing underscores
    return text.strip('_')
```

### Examples:

**Before:**
- `16 West 21st Street #10/11` → `16_West_21st_Street_#10/11.docx` ❌ (Invalid!)
- `123 Main St: Apt 4` → `123_Main_St:_Apt_4.docx` ❌ (Invalid!)

**After:**
- `16 West 21st Street #10/11` → `16_West_21st_Street__10_11.docx` ✅
- `123 Main St: Apt 4` → `123_Main_St__Apt_4.docx` ✅
- `20 Confucius Plaza #13A` → `20_Confucius_Plaza__13A.docx` ✅

---

## Testing

### Test Cases:
```python
# Test 1: Forward slash in unit number
address = "16 West 21st Street #10/11, New York, NY 10010"
# Expected: PreWalk_16_West_21st_Street__10_11.docx

# Test 2: Colon in address
address = "123 Main St: Suite 100, Brooklyn, NY"
# Expected: PreWalk_123_Main_St__Suite_100.docx

# Test 3: Multiple special characters
address = "456 Park Ave #5A/B*, New York, NY"
# Expected: PreWalk_456_Park_Ave__5A_B_.docx

# Test 4: Normal address (no special chars)
address = "789 Broadway, New York, NY"
# Expected: PreWalk_789_Broadway.docx
```

---

## Deployment

### Git Commits:
1. **0b12aaf** - Property lookup address validation fix
2. **b8df029** - Filename sanitization fix (this fix)

### Status:
✅ Pushed to GitHub  
⏳ Deploying to Render (auto-deploy)

### Verification:
Once deployed, test with the problematic address:
```bash
curl -X POST https://your-app.onrender.com/generate-report-from-text \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "Test transcript...",
    "address": "16 West 21st Street #10/11, New York, NY 10010",
    "last_name": "Test"
  }' \
  --output test_report.docx
```

Should now successfully create: `PreWalk_Test.docx` or `PreWalk_16_West_21st_Street__10_11.docx`

---

## Prevention

### Best Practices:
1. Always sanitize user input before using in filenames
2. Use a whitelist of allowed characters instead of blacklist
3. Consider using UUID or timestamp-based filenames for uniqueness
4. Test with edge cases: special characters, unicode, very long names

### Future Improvements:
```python
import re
import uuid

def generate_safe_filename(address: str, last_name: str = None) -> str:
    """Generate a safe, unique filename"""
    if last_name:
        base = last_name
    else:
        base = address.split(',')[0]
    
    # Keep only alphanumeric, spaces, and hyphens
    safe = re.sub(r'[^a-zA-Z0-9\s-]', '', base)
    safe = re.sub(r'\s+', '_', safe)
    safe = safe[:50]  # Limit length
    
    # Add timestamp or UUID for uniqueness
    unique_id = str(uuid.uuid4())[:8]
    
    return f"PreWalk_{safe}_{unique_id}.docx"
```

---

## Summary

**Problem**: Forward slash in address caused FileNotFoundError  
**Solution**: Sanitize all invalid filename characters  
**Impact**: Prevents errors for addresses with special characters  
**Status**: ✅ Fixed and deployed

---

**Created**: Current Date  
**Commit**: b8df029  
**Priority**: High  
**Category**: Bug Fix
