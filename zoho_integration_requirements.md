# Zoho Integration Requirements for Neighboring Projects Feature

## Zoho CRM Data Structure Analysis

### Required Information:
1. **Which Zoho product are you using?**
   - Zoho CRM
   - Zoho Projects
   - Zoho Books
   - Zoho Creator (custom app)

2. **Project Data Fields Needed:**
   - Project Address (full address)
   - Project Type (kitchen, bathroom, full renovation, etc.)
   - Project Status (completed, in-progress, contracted)
   - Completion Date / Contract Date
   - Budget Range (if available)
   - Client Name (for testimonials)
   - Project Photos (if stored in Zoho)
   - Project Description/Scope

3. **API Access Requirements:**
   - Zoho API credentials
   - OAuth 2.0 setup
   - API rate limits
   - Data access permissions

## Technical Implementation Options:

### Option 1: Zoho CRM API
```python
# Direct API integration
import requests

def get_zoho_projects():
    headers = {
        'Authorization': f'Zoho-oauthtoken {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Get all deals/projects
    response = requests.get(
        'https://www.zohoapis.com/crm/v2/Deals',
        headers=headers,
        params={
            'fields': 'Deal_Name,Closing_Date,Amount,Stage,Property_Address',
            'per_page': 200
        }
    )
    return response.json()
```

### Option 2: Zoho Webhook Integration
```python
# Real-time updates via webhooks
@app.post("/zoho-webhook")
async def handle_zoho_webhook(data: dict):
    # Process project updates
    # Cache project data locally
    pass
```

### Option 3: CSV Export Integration
```python
# Manual/scheduled CSV exports
import pandas as pd

def process_zoho_export(csv_file):
    df = pd.read_csv(csv_file)
    # Process project data
    return projects_list
```

## Questions to Answer:

1. **Zoho Setup:**
   - What's your Zoho domain? (e.g., yourcompany.zohocrm.com)
   - Do you have API access enabled?
   - What fields store project addresses?
   - How do you track project status?

2. **Data Structure:**
   - Are projects stored as "Deals" in CRM?
   - Do you have custom fields for project details?
   - Where are project photos stored?
   - How do you categorize project types?

3. **Access & Security:**
   - Can we create a dedicated API user?
   - What's your preferred authentication method?
   - Any IP restrictions on API access?
   - Data privacy requirements?

4. **Business Logic:**
   - What radius for "neighboring" projects? (1 mile, 5 miles, 10 miles?)
   - Which project statuses to include? (completed only, or in-progress too?)
   - Should we show client names or keep anonymous?
   - Any projects to exclude (confidential, etc.)?