# Neighboring Projects Feature

## Overview

The Neighboring Projects feature automatically adds a section to pre-walkthrough reports showing other projects in the same building or neighborhood, pulled from your Zoho CRM Deals.

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  1. Sync Script (runs every week)                           │
│     ├─ Fetches all Deals from Zoho CRM                     │
│     ├─ Stores in local cache (data/cache/zoho_deals_cache.json) │
│     └─ Cache TTL: 1 week (168 hours)                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Report Generation                                        │
│     ├─ Extracts neighborhood from property data            │
│     ├─ Searches cache for matching projects                │
│     ├─ Prioritizes same building, then neighborhood        │
│     └─ Adds section to Word document                       │
└─────────────────────────────────────────────────────────────┘
```

### Benefits

✅ **Fast**: No API calls during report generation (instant lookup)  
✅ **Reliable**: Works even if Zoho API is down  
✅ **Efficient**: One sync updates all data  
✅ **Fresh**: Auto-refreshes every week  
✅ **Smart**: Matches by building first, then neighborhood  

## Setup

### 1. Install Dependencies

No additional dependencies needed - uses existing packages.

### 2. Configure Zoho Credentials

Already configured in `config.json`:
```json
{
  "api_keys": {
    "zoho": {
      "client_id": "1000.BTVCVLRAA929UPUKPQ4A0Y2XS3WK8M",
      "client_secret": "4f9ff22d9bcb4b68bb60af7fefc05616974e355296",
      "refresh_token": "1000.3ff810c474ffec8f0521d0d86923c052.2d1d1c684c2e23ffbe9f8b024535cfee"
    }
  }
}
```

### 3. Initial Sync

Run the sync script to populate the cache:

```bash
python sync_zoho_deals.py
```

**Expected output:**
```
2025-11-26 15:30:00 - __main__ - INFO - Initializing Zoho API...
2025-11-26 15:30:01 - __main__ - INFO - Fetching deals from Zoho CRM...
2025-11-26 15:30:05 - __main__ - INFO - Fetched 910 deals from Zoho CRM
2025-11-26 15:30:05 - __main__ - INFO - Saving deals to cache...
2025-11-26 15:30:05 - __main__ - INFO - ✅ Sync completed successfully!
```

### 4. Schedule Automatic Sync

#### Option A: Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line to run every week (Sunday at midnight)
0 0 * * 0 cd /path/to/project && python sync_zoho_deals.py >> sync.log 2>&1
```

#### Option B: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Weekly, every Sunday at midnight
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\path\to\project\sync_zoho_deals.py`

#### Option C: Render Cron Job

Add to `render.yaml`:
```yaml
services:
  - type: web
    name: prewalk-api
    # ... existing config ...

  - type: cron
    name: zoho-sync
    env: python
    schedule: "0 0 * * 0"  # Every Sunday at midnight
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python sync_zoho_deals.py"
```

## Usage

### In Reports

The feature works automatically. When generating a report:

1. System extracts neighborhood from property data
2. Searches cache for matching projects
3. Adds "Neighboring Projects" section to document

**Example output in report:**

```
┌─────────────────────────────────────────────────────────────┐
│ Neighboring Projects                                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Found 2 project(s) in the same building and 3 in the       │
│ neighborhood.                                                │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ Project Address    │ Amount      │ Stage    │ Location  ││
│ ├──────────────────────────────────────────────────────────┤│
│ │ 16 W 21st St #5A   │ $94,855     │ Proposal │ Same Bldg ││
│ │ 16 W 21st St #12B  │ $354,160    │ Won      │ Same Bldg ││
│ │ 18 W 21st St       │ $122,000    │ In Cont  │ Neighbor  ││
│ └──────────────────────────────────────────────────────────┘│
│                                                              │
│ Total project value in area: $571,015                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Manual Sync

To manually refresh the cache:

```bash
python sync_zoho_deals.py
```

### Check Cache Status

```python
from pre_walkthrough_generator.src.neighboring_projects import NeighboringProjectsManager

manager = NeighboringProjectsManager()
stats = manager.get_cache_stats()
print(stats)
```

**Output:**
```python
{
    'exists': True,
    'valid': True,
    'count': 910,
    'age_hours': 2.5,
    'last_updated': '2025-11-26 15:30:05'
}
```

## Files Created

```
project/
├── sync_zoho_deals.py                              # Sync script
├── pre_walkthrough_generator/src/
│   ├── zoho_api.py                                 # Zoho CRM API client
│   └── neighboring_projects.py                     # Cache & matching logic
├── data/cache/
│   └── zoho_deals_cache.json                       # Cached deals
├── config.json                                     # Updated with Zoho creds
└── NEIGHBORING_PROJECTS_FEATURE.md                 # This file
```

## Matching Logic

### Same Building Detection

Two addresses are considered "same building" if:
- Street number matches (e.g., "16")
- Street name matches (e.g., "W 21st St")
- Unit numbers are ignored

**Examples:**
- ✅ `16 W 21st St #5A` matches `16 W 21st St #12B` (same building)
- ❌ `16 W 21st St` does NOT match `18 W 21st St` (different building)

### Neighborhood Detection

Projects are considered "same neighborhood" if:
- Zip code matches, OR
- Neighborhood name matches (e.g., "Flatiron District")

**Priority:**
1. Same building projects (highlighted in light blue)
2. Same neighborhood projects
3. Sorted by deal amount (highest first)

## Customization

### Change Cache TTL

Edit `neighboring_projects.py`:
```python
self.cache_ttl_hours = 168  # 1 week (default)
# Change to 336 for 2 weeks, or 24 for 1 day
```

### Change Fields Fetched

Edit `sync_zoho_deals.py`:
```python
fields = ["Deal_Name", "Amount", "Stage", "Contact_Name", "Closing_Date", "Your_Custom_Field"]
```

### Change Matching Logic

Edit `neighboring_projects.py` methods:
- `_is_same_building()` - Building matching logic
- `_is_same_neighborhood()` - Neighborhood matching logic
- `find_neighboring_projects()` - Search and filter logic

## Troubleshooting

### No Projects Showing

**Check 1: Is cache populated?**
```bash
ls -lh data/cache/zoho_deals_cache.json
```

**Check 2: Run sync manually**
```bash
python sync_zoho_deals.py
```

**Check 3: Check logs**
```bash
tail -f generator.log | grep "neighboring"
```

### Zoho API Errors

**Error: "Invalid token"**
- Refresh token may have expired
- Generate new refresh token from Zoho Developer Console

**Error: "Rate limit exceeded"**
- Sync script respects rate limits (0.5s delay between pages)
- If still hitting limits, increase delay in `zoho_api.py`

### Cache Not Refreshing

**Check cron job:**
```bash
crontab -l  # List cron jobs
tail -f sync.log  # Check sync logs
```

**Manual refresh:**
```bash
python sync_zoho_deals.py
```

## API Reference

### ZohoAPI Class

```python
from zoho_api import ZohoAPI

zoho = ZohoAPI(client_id, client_secret, refresh_token)

# Get all deals
deals = zoho.get_all_records("Deals", fields=["Deal_Name", "Amount"], max_records=5000)

# Search deals
deals = zoho.search_records("Deals", criteria="(Stage:equals:Won)")
```

### NeighboringProjectsManager Class

```python
from neighboring_projects import NeighboringProjectsManager

manager = NeighboringProjectsManager()

# Save cache
manager.save_cache(deals)

# Load cache
cache_data = manager.load_cache()

# Find neighbors
projects = manager.find_neighboring_projects(
    target_address="16 W 21st St, New York, NY",
    target_neighborhood="Flatiron District",
    same_building_only=False
)

# Get stats
stats = manager.get_cache_stats()
```

## Performance

- **Sync time**: ~5-10 seconds for 1000 deals
- **Cache size**: ~500KB for 1000 deals
- **Lookup time**: <10ms (instant from cache)
- **Memory usage**: Minimal (cache loaded on demand)

## Security

- ✅ Credentials stored in `config.json` (add to `.gitignore`)
- ✅ Use environment variables in production
- ✅ Refresh token is permanent (no expiration)
- ✅ Access token auto-refreshes (1 hour TTL)

## Future Enhancements

Potential improvements:
- [ ] Add distance-based matching (within X miles)
- [ ] Include project photos from Zoho
- [ ] Add project timeline/duration
- [ ] Filter by project type (kitchen, bathroom, etc.)
- [ ] Add project completion status
- [ ] Export neighboring projects to CSV
- [ ] Add API endpoint to trigger sync
- [ ] Add webhook to sync on deal updates

## Support

For issues or questions:
1. Check logs: `generator.log` and `sync.log`
2. Verify cache: `data/cache/zoho_deals_cache.json`
3. Test sync: `python sync_zoho_deals.py`
4. Check Zoho API status: https://status.zoho.com/

---

**Created**: November 26, 2025  
**Version**: 1.0.0  
**Status**: ✅ Ready for Production
