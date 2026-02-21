# Neighboring Projects Feature - Implementation Plan

## 🎯 Feature Overview

**Goal:** Add a "Neighboring Projects" section to walkthrough reports showing past/current projects near the property location.

**Business Value:**
- Builds client confidence through local experience
- Showcases company portfolio
- Demonstrates neighborhood expertise
- Provides social proof and credibility

## 🏗️ Architecture Design

### New Components to Build:

```
pre_walkthrough_generator/src/
├── zoho_api.py              # Zoho CRM integration
├── location_service.py      # Distance calculations
├── project_matcher.py       # Find neighboring projects
└── cache_manager.py         # Cache project data
```

### Updated Components:

```
pre_walkthrough_generator/src/
├── document_generator.py    # Add new section
└── fastapi_server.py       # New endpoints
```

## 📊 Data Flow

```
Current Property Address
        ↓
1. Get coordinates (Google Geocoding API)
        ↓
2. Fetch all projects from Zoho CRM
        ↓
3. Calculate distances to each project
        ↓
4. Filter projects within radius (e.g., 5 miles)
        ↓
5. Sort by distance (closest first)
        ↓
6. Format for document generation
        ↓
7. Add "Neighboring Projects" section to report
```

## 🔧 Implementation Steps

### Phase 1: Zoho Integration (Week 1)

#### Step 1.1: Create Zoho API Client
```python
# pre_walkthrough_generator/src/zoho_api.py

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os

class ZohoAPI:
    def __init__(self):
        self.client_id = os.getenv('ZOHO_CLIENT_ID')
        self.client_secret = os.getenv('ZOHO_CLIENT_SECRET')
        self.refresh_token = os.getenv('ZOHO_REFRESH_TOKEN')
        self.access_token = None
        self.token_expires = None
        self.base_url = "https://www.zohoapis.com/crm/v2"
    
    def get_access_token(self) -> str:
        """Get or refresh access token"""
        if self.access_token and self.token_expires > datetime.now():
            return self.access_token
        
        # Refresh token
        response = requests.post(
            "https://accounts.zoho.com/oauth/v2/token",
            data={
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            self.token_expires = datetime.now() + timedelta(seconds=data['expires_in'])
            return self.access_token
        else:
            raise Exception(f"Failed to refresh token: {response.text}")
    
    def get_projects(self, status_filter: List[str] = None) -> List[Dict]:
        """Fetch all projects from Zoho CRM"""
        headers = {
            'Authorization': f'Zoho-oauthtoken {self.get_access_token()}',
            'Content-Type': 'application/json'
        }
        
        projects = []
        page = 1
        per_page = 200
        
        while True:
            response = requests.get(
                f"{self.base_url}/Deals",
                headers=headers,
                params={
                    'fields': 'Deal_Name,Closing_Date,Amount,Stage,Property_Address,Project_Type,Description,Owner',
                    'per_page': per_page,
                    'page': page
                }
            )
            
            if response.status_code != 200:
                break
                
            data = response.json()
            if 'data' not in data:
                break
                
            batch_projects = data['data']
            
            # Filter by status if specified
            if status_filter:
                batch_projects = [p for p in batch_projects if p.get('Stage') in status_filter]
            
            projects.extend(batch_projects)
            
            # Check if more pages
            if len(batch_projects) < per_page:
                break
                
            page += 1
        
        return projects
    
    def get_project_photos(self, project_id: str) -> List[str]:
        """Get photos for a specific project"""
        headers = {
            'Authorization': f'Zoho-oauthtoken {self.get_access_token()}',
        }
        
        response = requests.get(
            f"{self.base_url}/Deals/{project_id}/Attachments",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            photos = []
            for attachment in data.get('data', []):
                if attachment.get('File_Name', '').lower().endswith(('.jpg', '.jpeg', '.png')):
                    photos.append(attachment.get('$download_url'))
            return photos
        
        return []
```

#### Step 1.2: Create Location Service
```python
# pre_walkthrough_generator/src/location_service.py

import requests
import math
from typing import Tuple, Optional
import os

class LocationService:
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """Get latitude and longitude for an address"""
        if not self.google_api_key:
            return None
            
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                'address': address,
                'key': self.google_api_key
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                location = data['results'][0]['geometry']['location']
                return (location['lat'], location['lng'])
        
        return None
    
    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in miles"""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Haversine formula
        R = 3959  # Earth's radius in miles
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return round(distance, 2)
```

#### Step 1.3: Create Project Matcher
```python
# pre_walkthrough_generator/src/project_matcher.py

from typing import List, Dict, Optional
from .zoho_api import ZohoAPI
from .location_service import LocationService
import logging

class ProjectMatcher:
    def __init__(self):
        self.zoho_api = ZohoAPI()
        self.location_service = LocationService()
        self.logger = logging.getLogger(__name__)
    
    def find_neighboring_projects(self, 
                                current_address: str, 
                                radius_miles: float = 5.0,
                                max_projects: int = 10) -> List[Dict]:
        """Find projects within radius of current address"""
        
        try:
            # Get coordinates for current address
            current_coords = self.location_service.get_coordinates(current_address)
            if not current_coords:
                self.logger.warning(f"Could not geocode address: {current_address}")
                return []
            
            # Get all projects from Zoho
            all_projects = self.zoho_api.get_projects(
                status_filter=['Closed Won', 'In Progress', 'Contracted']
            )
            
            neighboring_projects = []
            
            for project in all_projects:
                project_address = project.get('Property_Address')
                if not project_address:
                    continue
                
                # Get coordinates for project address
                project_coords = self.location_service.get_coordinates(project_address)
                if not project_coords:
                    continue
                
                # Calculate distance
                distance = self.location_service.calculate_distance(
                    current_coords, project_coords
                )
                
                # Check if within radius
                if distance <= radius_miles:
                    project_data = {
                        'address': project_address,
                        'distance_miles': distance,
                        'project_name': project.get('Deal_Name', 'Unnamed Project'),
                        'project_type': project.get('Project_Type', 'Renovation'),
                        'status': project.get('Stage', 'Unknown'),
                        'completion_date': project.get('Closing_Date'),
                        'budget_range': self._format_budget(project.get('Amount')),
                        'description': project.get('Description', ''),
                        'project_id': project.get('id')
                    }
                    
                    # Get photos if available
                    photos = self.zoho_api.get_project_photos(project.get('id'))
                    project_data['photos'] = photos[:3]  # Limit to 3 photos
                    
                    neighboring_projects.append(project_data)
            
            # Sort by distance and limit results
            neighboring_projects.sort(key=lambda x: x['distance_miles'])
            return neighboring_projects[:max_projects]
            
        except Exception as e:
            self.logger.error(f"Error finding neighboring projects: {str(e)}")
            return []
    
    def _format_budget(self, amount: Optional[float]) -> str:
        """Format budget amount for display"""
        if not amount:
            return "Budget not disclosed"
        
        if amount < 50000:
            return f"${amount:,.0f}"
        elif amount < 100000:
            return f"${amount/1000:.0f}K"
        else:
            return f"${amount/1000:.0f}K+"
```

### Phase 2: Document Integration (Week 2)

#### Step 2.1: Update Document Generator
```python
# Add to pre_walkthrough_generator/src/document_generator.py

def _add_neighboring_projects(self, data: Dict[str, Any]):
    """Add neighboring projects section"""
    neighboring_projects = data.get('neighboring_projects', [])
    
    if not neighboring_projects:
        return
    
    # Add section heading
    heading = self.doc.add_heading('Neighboring Projects', level=1)
    heading.style.font.color.rgb = RGBColor(0, 51, 102)  # Dark blue
    
    # Add intro paragraph
    intro = self.doc.add_paragraph()
    intro.add_run("Our company has successfully completed projects in your neighborhood, "
                 "demonstrating our local expertise and commitment to quality work.")
    
    # Create table for projects
    table = self.doc.add_table(rows=1, cols=5)
    table.style = 'Light Grid Accent 1'
    
    # Header row
    header_cells = table.rows[0].cells
    header_cells[0].text = 'Address'
    header_cells[1].text = 'Distance'
    header_cells[2].text = 'Project Type'
    header_cells[3].text = 'Status'
    header_cells[4].text = 'Completed'
    
    # Add project rows
    for project in neighboring_projects:
        row_cells = table.add_row().cells
        row_cells[0].text = project.get('address', '')
        row_cells[1].text = f"{project.get('distance_miles', 0)} miles"
        row_cells[2].text = project.get('project_type', '')
        row_cells[3].text = project.get('status', '')
        row_cells[4].text = project.get('completion_date', '')
    
    # Add project highlights
    if len(neighboring_projects) > 0:
        self.doc.add_paragraph()
        highlights = self.doc.add_paragraph()
        highlights.add_run("Project Highlights:").bold = True
        
        for i, project in enumerate(neighboring_projects[:3], 1):
            highlight = self.doc.add_paragraph(style='List Bullet')
            highlight.add_run(f"{project.get('address', '')}: ")
            highlight.add_run(project.get('description', 'Quality renovation completed on time and within budget.'))
```

### Phase 3: API Integration (Week 2)

#### Step 3.1: Update FastAPI Server
```python
# Add to fastapi_server.py

from pre_walkthrough_generator.src.project_matcher import ProjectMatcher

# Add new endpoint
@app.get("/neighboring-projects")
async def get_neighboring_projects(address: str, radius: float = 5.0):
    """Get neighboring projects for an address"""
    try:
        matcher = ProjectMatcher()
        projects = matcher.find_neighboring_projects(address, radius)
        return {"projects": projects, "count": len(projects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Update main generation function
async def generate_report_internal(transcript_text: str, address: str = None, last_name: str = None):
    # ... existing code ...
    
    # Add neighboring projects
    if address:
        try:
            matcher = ProjectMatcher()
            neighboring_projects = matcher.find_neighboring_projects(address)
            extracted_data['neighboring_projects'] = neighboring_projects
        except Exception as e:
            logger.warning(f"Could not fetch neighboring projects: {str(e)}")
            extracted_data['neighboring_projects'] = []
    
    # ... rest of existing code ...
```

## 🔐 Environment Variables

Add to `.env` file:
```bash
# Zoho CRM Integration
ZOHO_CLIENT_ID=your_zoho_client_id
ZOHO_CLIENT_SECRET=your_zoho_client_secret
ZOHO_REFRESH_TOKEN=your_zoho_refresh_token

# Google Maps API (for geocoding)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Neighboring Projects Settings
NEIGHBORING_PROJECTS_RADIUS=5.0
MAX_NEIGHBORING_PROJECTS=10
```

## 📦 Dependencies

Add to `requirements.txt`:
```
googlemaps==4.10.0
geopy==2.4.1
```

## 🧪 Testing Strategy

### Unit Tests:
```python
# tests/test_neighboring_projects.py

def test_zoho_api_connection():
    # Test Zoho API connectivity
    pass

def test_distance_calculation():
    # Test location service
    pass

def test_project_matching():
    # Test project filtering logic
    pass
```

### Integration Tests:
```python
def test_end_to_end_neighboring_projects():
    # Test full workflow
    pass
```

## 📈 Success Metrics

- **Client Engagement**: Track if reports with neighboring projects get better response rates
- **Conversion Rate**: Monitor if this feature improves deal closure rates
- **API Performance**: Monitor response times and error rates
- **Data Quality**: Track geocoding success rates

## 🚀 Deployment Plan

1. **Development**: Build and test locally
2. **Staging**: Deploy to test environment
3. **Production**: Gradual rollout with feature flag
4. **Monitoring**: Set up alerts and dashboards

## 💡 Future Enhancements

- **Interactive Map**: Show projects on a map
- **Project Photos**: Include before/after photos
- **Client Testimonials**: Add reviews from neighboring projects
- **Project Timeline**: Show project duration and phases
- **Cost Comparisons**: Show budget ranges for similar projects