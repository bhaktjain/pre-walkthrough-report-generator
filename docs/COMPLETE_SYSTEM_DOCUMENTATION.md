# Pre-Walkthrough Report Generator - Complete System Documentation

**Version:** 1.0.0  
**Last Updated:** November 25, 2025  
**Author:** System Documentation Team

---

## Table of Contents

1. [Executive Overview](#executive-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Core Components](#core-components)
5. [API Documentation](#api-documentation)
6. [Power Automate Integration](#power-automate-integration)
7. [Deployment Guide](#deployment-guide)
8. [Configuration Management](#configuration-management)
9. [Data Flow & Processing Pipeline](#data-flow--processing-pipeline)
10. [Security & Best Practices](#security--best-practices)
11. [Troubleshooting](#troubleshooting)
12. [Appendices](#appendices)

---

## Executive Overview

### Purpose
The Pre-Walkthrough Report Generator is an AI-powered automation system that transforms renovation consultation transcripts into professional, comprehensive pre-walkthrough reports for real estate and construction professionals.

### Key Capabilities
- **Automated Transcript Processing**: Extracts structured information from unstructured consultation transcripts
- **Property Data Enrichment**: Fetches real-time property details, photos, and floor plans
- **Professional Document Generation**: Creates formatted Word documents with embedded images and hyperlinks
- **RESTful API**: Easy integration with existing workflows and automation platforms
- **Multi-Platform Deployment**: Supports Render, Railway, Fly.io, and Azure

### Business Value
- **Time Savings**: Reduces report generation from 2-3 hours to under 2 minutes
- **Consistency**: Ensures standardized report format across all projects
- **Accuracy**: AI-powered extraction minimizes human error
- **Scalability**: Handles unlimited concurrent requests via cloud deployment

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  • Power Automate Flow                                           │
│  • Direct API Calls (cURL, Postman, Python)                     │
│  • CLI Interface (Local Development)                             │
│  • File Upload (Web Interface)                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI SERVER LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  • Request Validation (Pydantic)                                 │
│  • File Handling (Multipart/Form-Data)                          │
│  • Error Handling & Logging                                      │
│  • Metrics Tracking                                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PROCESSING LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  TRANSCRIPT PROCESSOR (transcript_processor.py)          │  │
│  │  • OpenAI GPT-4o Integration                             │  │
│  │  • Structured Data Extraction                            │  │
│  │  • Address Parsing & Validation                          │  │
│  │  • Client Profile Analysis                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                       │
│                           ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PROPERTY API (property_api.py)                          │  │
│  │  • Web Scraping (DuckDuckGo, Realtor.com)               │  │
│  │  • RapidAPI Integration                                  │  │
│  │  • Property ID Resolution                                │  │
│  │  • Image & Floor Plan Fetching                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                       │
│                           ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DOCUMENT GENERATOR (document_generator.py)              │  │
│  │  • Word Document Assembly                                │  │
│  │  • Image Embedding & Conversion                          │  │
│  │  • Table Formatting                                      │  │
│  │  • Hyperlink Creation                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
├─────────────────────────────────────────────────────────────────┤
│  • OpenAI API (GPT-4o)                                           │
│  • RapidAPI (US Real Estate Listings)                           │
│  • SerpAPI (Optional - Google Search)                           │
│  • DuckDuckGo (Free Web Search)                                 │
│  • Realtor.com (Property Data)                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  • Word Document (.docx)                                         │
│  • JSON Response (API)                                           │
│  • File Download (HTTP Response)                                 │
│  • Power Automate Connector                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Request Reception**: FastAPI receives transcript via API endpoint
2. **Transcript Processing**: OpenAI extracts structured data
3. **Property Enrichment**: Multi-source property data fetching
4. **Document Assembly**: Professional Word document generation
5. **Response Delivery**: File download or API response

---

## Technology Stack

### Backend Framework
- **FastAPI 0.104.1**: Modern, high-performance Python web framework
  - Async/await support for concurrent processing
  - Automatic API documentation (Swagger/OpenAPI)
  - Built-in request validation with Pydantic
  - WebSocket support for real-time updates

- **Uvicorn 0.24.0**: Lightning-fast ASGI server
  - Production-grade performance
  - HTTP/1.1 and HTTP/2 support
  - WebSocket protocol support

- **Gunicorn 21.2.0**: WSGI HTTP server for production
  - Process management
  - Worker lifecycle management
  - Graceful restarts

### AI & Machine Learning
- **OpenAI API 1.3.7**: GPT-4o model integration
  - Natural language understanding
  - Structured data extraction
  - JSON mode for reliable parsing
  - 4,000 token output capacity

### Document Processing
- **python-docx 1.1.0**: Word document manipulation
  - Document creation and modification
  - Table and paragraph formatting
  - Image embedding
  - Hyperlink creation

- **Pillow 10.1.0**: Image processing library
  - Format conversion (JPEG, PNG, WebP)
  - Image resizing and optimization
  - Color space management

### Web Scraping & HTTP
- **BeautifulSoup4**: HTML/XML parsing
  - CSS selector support
  - Robust HTML parsing
  - Tag navigation and searching

- **lxml**: Fast XML/HTML parser
  - C-based parser for performance
  - XPath support

- **Requests 2.31.0**: HTTP library
  - Session management
  - Connection pooling
  - Retry logic support

- **httpx 0.25.2**: Modern async HTTP client
  - HTTP/2 support
  - Connection pooling
  - Timeout management

### Data Validation & Configuration
- **Pydantic 2.5.0**: Data validation using Python type hints
  - Automatic validation
  - JSON schema generation
  - Settings management

- **python-dotenv 1.0.0**: Environment variable management
  - .env file loading
  - Configuration isolation

### Logging & Monitoring
- **python-json-logger 2.0.7**: Structured JSON logging
  - Machine-readable logs
  - Easy log aggregation

- **structlog 23.2.0**: Structured logging
  - Context preservation
  - Log enrichment

- **prometheus-client 0.19.0**: Metrics collection
  - Request counters
  - Response time histograms
  - Custom metrics

### File Handling
- **python-multipart 0.0.6**: Multipart form data parsing
  - File upload handling
  - Streaming support

- **aiofiles 23.2.1**: Async file operations
  - Non-blocking file I/O
  - Better performance for large files

### External APIs & Services

#### OpenAI API
- **Model**: GPT-4o (gpt-4o)
- **Purpose**: Transcript analysis and structured data extraction
- **Pricing**: $5.00 per 1M input tokens, $15.00 per 1M output tokens
- **Rate Limits**: 10,000 requests per minute (tier-dependent)

#### RapidAPI - US Real Estate Listings
- **Endpoints Used**:
  - `/v2/property` - Property details
  - `/propertyPhotos` - Images and floor plans
- **Pricing**: Varies by plan (Basic: $0/month with limits)
- **Rate Limits**: Plan-dependent

#### SerpAPI (Optional)
- **Purpose**: Enhanced Google search for property URLs
- **Pricing**: $50/month for 5,000 searches
- **Alternative**: Free DuckDuckGo scraping

### Deployment Platforms

#### Render (Primary)
- **Type**: Platform as a Service (PaaS)
- **Features**:
  - Automatic deployments from Git
  - Free SSL certificates
  - Environment variable management
  - Health checks and auto-restart

#### Railway (Alternative)
- **Type**: Platform as a Service
- **Features**:
  - Git-based deployments
  - Automatic HTTPS
  - Usage-based pricing

#### Fly.io (Alternative)
- **Type**: Edge computing platform
- **Features**:
  - Global distribution
  - Low latency
  - Docker-based deployments

#### Azure Functions (Serverless Option)
- **Type**: Function as a Service (FaaS)
- **Features**:
  - Event-driven execution
  - Auto-scaling
  - Pay-per-execution

### Development Tools
- **Python 3.11+**: Programming language
- **Git**: Version control
- **Docker**: Containerization (optional)
- **Postman**: API testing
- **ngrok**: Local tunnel for testing webhooks

---

## Core Components

### 1. FastAPI Server (`fastapi_server.py`)

**Purpose**: Main application server handling HTTP requests and orchestrating the report generation pipeline.

**Key Features**:
- RESTful API endpoints
- Request validation and error handling
- File upload processing
- Metrics tracking
- Health monitoring

**Endpoints**:

```python
GET  /                          # Root health check
GET  /health                    # Comprehensive health status
GET  /metrics                   # Server metrics
GET  /config                    # Current configuration
POST /generate-report           # Generate from file upload
POST /generate-report-from-text # Generate from JSON text
POST /config/reload             # Reload configuration
PUT  /config/api-keys          # Update API keys
PUT  /config/settings          # Update server settings
POST /templates/upload         # Upload custom template
```

**Request/Response Examples**:

```bash
# Health Check
curl https://your-app.onrender.com/health

# Response
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "requests_processed": 42,
  "errors": 0,
  "last_request": "2025-11-25T10:30:00",
  "timestamp": "2025-11-25T11:30:00"
}

# Generate Report from Text
curl -X POST https://your-app.onrender.com/generate-report-from-text \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "We visited 123 Main St today...",
    "address": "123 Main St, Brooklyn, NY 11201",
    "last_name": "Smith"
  }' \
  --output report.docx
```

---

### 2. Transcript Processor (`transcript_processor.py`)

**Purpose**: Extracts structured information from unstructured consultation transcripts using OpenAI GPT-4o.

**Key Methods**:

```python
extract_info(transcript: str) -> Dict[str, Any]
    # Extracts comprehensive renovation details
    # Returns: Structured JSON with all consultation data

extract_address(transcript: str) -> str
    # Extracts and validates property address
    # Returns: Cleaned, standardized address

analyze_client(transcript: str) -> Dict[str, Any]
    # Analyzes client behavior and red flags
    # Returns: Client profile and risk assessment

clean_transcript(transcript: str) -> str
    # Removes timestamps and formatting artifacts
    # Returns: Clean text for processing
```

**Extraction Schema**:

```json
{
  "property_address": "string",
  "property_info": {
    "building_type": "string",
    "total_units": "number|null",
    "year_built": "number|null",
    "building_rules": ["string"],
    "building_features": ["string"]
  },
  "client_info": {
    "names": ["string"],
    "phone": "string",
    "profession": "string",
    "preferences": {
      "budget_sensitivity": "low|medium|high",
      "decision_making": "quick|moderate|slow",
      "design_involvement": "low|medium|high",
      "quality_preference": "basic|mid-range|luxury"
    },
    "constraints": ["string"],
    "red_flags": {
      "is_negative_reviewer": "boolean",
      "payment_concerns": "boolean",
      "unrealistic_expectations": "boolean",
      "communication_issues": "boolean"
    }
  },
  "renovation_scope": {
    "kitchen": {
      "description": "string",
      "estimated_cost": {
        "range": {"min": "number", "max": "number|null"}
      },
      "plumbing_changes": "string",
      "electrical_changes": "string",
      "specific_requirements": ["string"],
      "appliances": ["string"],
      "cabinets_and_countertops": {
        "type": "string",
        "preferences": ["string"]
      }
    },
    "bathrooms": {
      "count": "number|null",
      "cost_per_bathroom": "number|null",
      "plumbing_changes": "string",
      "specific_requirements": ["string"],
      "fixtures": ["string"],
      "finishes": ["string"]
    },
    "additional_work": {
      "rooms": ["string"],
      "structural_changes": ["string"],
      "systems_updates": ["string"],
      "custom_features": ["string"],
      "estimated_costs": {
        "per_sqft_cost": "number|null",
        "total_estimated_range": {
          "min": "number|null",
          "max": "number|null"
        },
        "architect_fees": {
          "percentage": "number|null",
          "estimated_amount": "number|null"
        }
      }
    },
    "timeline": {
      "total_duration": "string",
      "phasing": "string",
      "living_arrangements": "string",
      "constraints": ["string"],
      "key_dates": {
        "survey_completion": "string",
        "walkthrough_scheduled": "string",
        "project_start": "string",
        "other_milestones": ["string"]
      }
    }
  },
  "materials_and_design": {
    "sourcing_responsibility": "string",
    "specific_materials": ["string"],
    "style_preferences": ["string"],
    "quality_preferences": ["string"]
  },
  "project_management": {
    "client_involvement": "string",
    "design_services": ["string"],
    "documentation_needs": ["string"],
    "permit_requirements": ["string"],
    "company_details": {
      "company_name": "string",
      "contact_person": "string",
      "services_offered": ["string"],
      "fees_structure": ["string"]
    }
  }
}
```

**AI Prompt Engineering**:
- Uses GPT-4o with `temperature=0` for consistency
- JSON mode enabled for structured output
- 4,000 token max output for comprehensive extraction
- Handles multiple project types (kitchen, bathroom, whole-house, commercial)

---

### 3. Property API (`property_api.py`)

**Purpose**: Fetches property details, photos, and floor plans from multiple sources with intelligent fallback strategies.

**Key Methods**:

```python
get_all_property_data(address: str) -> Dict[str, Any]
    # One-call method to fetch all property data
    # Returns: Complete property information package

get_property_id(address: str) -> Optional[str]
    # Resolves property ID using web scraping
    # Returns: Numeric property ID (e.g., "12345678")

get_property_details(property_id: str) -> Dict[str, Any]
    # Fetches detailed property information via RapidAPI
    # Returns: Property specs, pricing, features

get_property_photos(property_id: str) -> Dict[str, Any]
    # Fetches property images and floor plans
    # Returns: Separated images and floor plans

get_realtor_link(address: str) -> Optional[str]
    # Gets canonical Realtor.com URL
    # Returns: Full listing URL

build_realtor_url(property_id: str, address: str) -> Optional[str]
    # Constructs Realtor.com URL from components
    # Returns: Formatted listing URL
```

**Property ID Resolution Strategy** (Cost-Free):

```
1. DuckDuckGo Web Scraping (Primary)
   ├─ Search: "{address} site:realtor.com"
   ├─ Parse HTML results
   └─ Extract property ID from URL pattern

2. Realtor.com Site Search (Fallback)
   ├─ Direct search on Realtor.com
   ├─ Parse search results page
   └─ Extract first matching listing

3. SerpAPI Google Search (Optional)
   ├─ Requires API key ($50/month)
   ├─ More reliable results
   └─ Higher rate limits

4. URL Construction (Last Resort)
   ├─ Use extracted property ID
   ├─ Slugify address components
   └─ Build canonical URL
```

**RapidAPI Integration**:

```python
# Endpoint: /v2/property
# Purpose: Get comprehensive property details
# Rate Limit: Plan-dependent
# Response Time: ~1-2 seconds

# Endpoint: /propertyPhotos
# Purpose: Get property images and floor plans
# Rate Limit: Plan-dependent
# Response Time: ~1-2 seconds
```

**Address Slugification**:

```python
# Input: "123 West 45th Street, Apt 8A, New York, NY 10036"
# Output: "123-W-45th-St_New-York_NY_10036"

# Rules:
# 1. Remove apartment/unit numbers
# 2. Abbreviate directions (West → W)
# 3. Abbreviate street types (Street → St)
# 4. Replace spaces with hyphens
# 5. Separate components with underscores
```

**Error Handling**:
- Retry logic with exponential backoff
- Multiple search query variations
- Graceful degradation (missing data → "Information not available")
- BeautifulSoup4 optional dependency check

---

### 4. Document Generator (`document_generator.py`)

**Purpose**: Assembles professional Word documents with formatted tables, embedded images, and hyperlinks.

**Key Methods**:

```python
generate_report(data: Dict[str, Any], output_dir: str, file_name: str) -> str
    # Main report generation method
    # Returns: Path to generated .docx file

_add_executive_summary(data: Dict[str, Any])
    # Creates sales-focused project overview
    # Includes: Goals, drivers, key numbers

_add_property_details(data: Dict[str, Any])
    # Formats property information table
    # Includes: Price, sqft, bed/bath, HOA

_add_client_details(data: Dict[str, Any])
    # Formats client profile table
    # Includes: Contact, preferences, red flags

_add_renovation_scope(data: Dict[str, Any])
    # Dynamic scope tables
    # Includes: Kitchen, bathrooms, additional work

_add_budget_summary(data: Dict[str, Any])
    # Cost breakdown table
    # Includes: Line items, totals, ranges

_download_image(url: str) -> Optional[BytesIO]
    # Downloads and converts images
    # Supports: JPEG, PNG, WebP → PNG conversion
```

**Document Structure**:

```
┌─────────────────────────────────────────┐
│ Header Image (0.8" height)              │
├─────────────────────────────────────────┤
│ Pre-Walkthrough Report                  │
│ [Property Address]                      │
│ [Date]                                  │
├─────────────────────────────────────────┤
│ Executive Summary                       │
│  • Project Goals                        │
│  • Client Drivers                       │
│  • Key Numbers (Budget + Timeline)      │
├─────────────────────────────────────────┤
│ Property Details                        │
│  [Formatted Table]                      │
├─────────────────────────────────────────┤
│ Client Details                          │
│  [Formatted Table]                      │
├─────────────────────────────────────────┤
│ Property Links                          │
│  • Realtor.com: [Hyperlink]            │
├─────────────────────────────────────────┤
│ Floor Plan                              │
│  [Embedded Image - 6" width]           │
│  [Image URL Link]                       │
├─────────────────────────────────────────┤
│ Building Requirements                   │
│  • [Dynamic rules from transcript]      │
├─────────────────────────────────────────┤
│ Renovation Scope                        │
│  Kitchen [Table]                        │
│  Bathrooms [Table]                      │
│  Additional Work [Table]                │
├─────────────────────────────────────────┤
│ Timeline & Phasing                      │
│  [Formatted Table]                      │
├─────────────────────────────────────────┤
│ Budget Summary                          │
│  [Cost Breakdown Table]                 │
├─────────────────────────────────────────┤
│ Notes                                   │
│  • [Material sourcing]                  │
│  • [Special requirements]               │
│  • [Communication preferences]          │
├─────────────────────────────────────────┤
│ Footer Image (0.8" height)              │
└─────────────────────────────────────────┘
```

**Formatting Features**:
- Custom heading styles (3 levels)
- Currency formatting with commas
- Hyperlink creation with blue underline
- Image embedding with size control
- Table styling with borders
- Section breaks for readability

---

### 5. Configuration Manager (`config_manager.py`)

**Purpose**: Dynamic configuration management with runtime updates.

**Features**:
- JSON-based configuration storage
- Environment variable override
- Runtime configuration updates
- API key management
- Settings persistence

**Configuration Schema**:

```json
{
  "api_keys": {
    "openai": "sk-...",
    "rapidapi": "...",
    "serpapi": "..."
  },
  "settings": {
    "max_file_size": 10485760,
    "timeout": 300,
    "enable_logging": true,
    "log_level": "INFO"
  },
  "templates": {
    "default_template": "Pre-walkthrough_template.docx"
  }
}
```

**Usage**:

```python
from config_manager import config_manager

# Get configuration value
api_key = config_manager.get("api_keys.openai")

# Set configuration value
config_manager.set("settings.timeout", 600)

# Update API keys
config_manager.update_api_keys(
    openai_key="sk-new-key",
    rapidapi_key="new-rapid-key"
)

# Reload from file
config_manager.reload_config()
```

---

## API Documentation

### Base URL
```
Production: https://your-app.onrender.com
Local: http://localhost:8000
```

### Authentication
Currently no authentication required. For production, consider adding:
- API key authentication
- OAuth 2.0
- JWT tokens

---

### Endpoints

#### 1. Health Check

**GET** `/health`

Returns comprehensive server health status.

**Response**:
```json
{
  "status": "healthy",
  "uptime_seconds": 3600.5,
  "requests_processed": 42,
  "errors": 0,
  "last_request": "2025-11-25T10:30:00",
  "timestamp": "2025-11-25T11:30:00"
}
```

**Status Codes**:
- `200 OK`: Server is healthy

---

#### 2. Generate Report from File

**POST** `/generate-report`

Generates a pre-walkthrough report from an uploaded transcript file.

**Request**:
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `transcript_file` (required): File upload (txt, docx, pdf)
  - `address` (optional): Property address string
  - `last_name` (optional): Client last name for filename

**cURL Example**:
```bash
curl -X POST https://your-app.onrender.com/generate-report \
  -F "transcript_file=@transcript.txt" \
  -F "address=123 Main St, Brooklyn, NY 11201" \
  -F "last_name=Smith" \
  --output PreWalkReport_Smith.docx
```

**Python Example**:
```python
import requests

url = "https://your-app.onrender.com/generate-report"
files = {"transcript_file": open("transcript.txt", "rb")}
data = {
    "address": "123 Main St, Brooklyn, NY 11201",
    "last_name": "Smith"
}

response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    with open("report.docx", "wb") as f:
        f.write(response.content)
    print("Report generated successfully!")
```

**Response**:
- **Content-Type**: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Body**: Binary Word document (.docx)

**Status Codes**:
- `200 OK`: Report generated successfully
- `400 Bad Request`: Invalid input (empty transcript, invalid file)
- `500 Internal Server Error`: Processing error

---

#### 3. Generate Report from Text

**POST** `/generate-report-from-text`

Generates a pre-walkthrough report from transcript text (JSON payload).

**Request**:
- **Content-Type**: `application/json`
- **Body**:
```json
{
  "transcript_text": "We visited the property at 123 Main St today...",
  "address": "123 Main St, Brooklyn, NY 11201",
  "last_name": "Smith"
}
```

**Parameters**:
- `transcript_text` (required): Full transcript text
- `address` (optional): Property address
- `last_name` (optional): Client last name

**cURL Example**:
```bash
curl -X POST https://your-app.onrender.com/generate-report-from-text \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "We visited 123 Main St today. The client wants to renovate the kitchen with a budget of $50,000...",
    "address": "123 Main St, Brooklyn, NY 11201",
    "last_name": "Johnson"
  }' \
  --output report.docx
```

**JavaScript Example**:
```javascript
const response = await fetch('https://your-app.onrender.com/generate-report-from-text', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    transcript_text: 'We visited 123 Main St today...',
    address: '123 Main St, Brooklyn, NY 11201',
    last_name: 'Johnson'
  })
});

const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'report.docx';
a.click();
```

**Response**:
- **Content-Type**: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Body**: Binary Word document (.docx)

**Status Codes**:
- `200 OK`: Report generated successfully
- `400 Bad Request`: Empty or invalid transcript
- `500 Internal Server Error`: Processing error

---

#### 4. Get Configuration

**GET** `/config`

Returns current server configuration (API keys masked).

**Response**:
```json
{
  "api_keys": {
    "openai": "sk-***",
    "rapidapi": "***",
    "serpapi": "***"
  },
  "settings": {
    "max_file_size": 10485760,
    "timeout": 300,
    "enable_logging": true,
    "log_level": "INFO"
  },
  "templates": {
    "default_template": "Pre-walkthrough_template.docx"
  }
}
```

---

#### 5. Update API Keys

**PUT** `/config/api-keys`

Updates API keys dynamically without restart.

**Request**:
- **Content-Type**: `application/x-www-form-urlencoded`
- **Parameters**:
  - `openai_key` (optional): New OpenAI API key
  - `rapidapi_key` (optional): New RapidAPI key
  - `serpapi_key` (optional): New SerpAPI key

**cURL Example**:
```bash
curl -X PUT https://your-app.onrender.com/config/api-keys \
  -d "openai_key=sk-new-key" \
  -d "rapidapi_key=new-rapid-key"
```

**Response**:
```json
{
  "message": "API keys updated successfully"
}
```

---

#### 6. Get Metrics

**GET** `/metrics`

Returns detailed server metrics and statistics.

**Response**:
```json
{
  "server_metrics": {
    "start_time": "2025-11-25T08:00:00",
    "requests_processed": 156,
    "errors": 3,
    "last_request": "2025-11-25T11:30:00"
  },
  "config": {
    "api_keys": {"openai": "sk-***"},
    "settings": {"timeout": 300}
  },
  "memory_usage": "Available via system monitoring"
}
```

---

### Error Responses

All endpoints return consistent error format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Error Codes**:
- `400 Bad Request`: Invalid input data
- `404 Not Found`: Endpoint doesn't exist
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: External API failure

---

### Rate Limiting

**Current Limits**:
- No rate limiting implemented
- Recommended: 100 requests per minute per IP

**Future Implementation**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/generate-report")
@limiter.limit("10/minute")
async def generate_report(...):
    ...
```

---

### API Versioning

**Current Version**: v1 (implicit)

**Future Versioning Strategy**:
```
/v1/generate-report
/v2/generate-report
```

---

## Power Automate Integration

### Overview

Power Automate (formerly Microsoft Flow) enables no-code automation workflows that can trigger the report generation system from various sources like email, SharePoint, OneDrive, or scheduled triggers.

---

### Use Cases

1. **Email-Triggered Reports**
   - Receive transcript via email attachment
   - Automatically generate and send report back

2. **SharePoint Integration**
   - Upload transcript to SharePoint folder
   - Auto-generate report and save to document library

3. **Scheduled Batch Processing**
   - Process all transcripts in a folder daily
   - Generate reports for multiple properties

4. **CRM Integration**
   - Trigger from Dynamics 365 or Salesforce
   - Attach report to customer record

---

### Power Automate Flow Setup

#### Flow 1: Email-to-Report Automation

**Trigger**: When a new email arrives with attachment

**Steps**:

1. **Trigger: When a new email arrives (V3)**
   - Folder: Inbox
   - Include Attachments: Yes
   - Subject Filter: Contains "Transcript" or "Pre-Walk"

2. **Condition: Check if attachment exists**
   - Condition: `length(triggerOutputs()?['body/attachments'])` is greater than 0

3. **Apply to each: Process attachments**
   - Select output: `Attachments`

4. **Condition: Check file type**
   - Condition: `items('Apply_to_each')?['name']` ends with `.txt`

5. **HTTP: Call API to generate report**
   - Method: POST
   - URI: `https://your-app.onrender.com/generate-report-from-text`
   - Headers:
     ```json
     {
       "Content-Type": "application/json"
     }
     ```
   - Body:
     ```json
     {
       "transcript_text": "@{base64ToString(items('Apply_to_each')?['contentBytes'])}",
       "address": "@{triggerOutputs()?['body/subject']}",
       "last_name": "@{triggerOutputs()?['body/from']}"
     }
     ```

6. **Send an email (V2)**
   - To: `@{triggerOutputs()?['body/from']}`
   - Subject: `Pre-Walkthrough Report - @{triggerOutputs()?['body/subject']}`
   - Body: `Your report is attached.`
   - Attachments:
     - Name: `PreWalkReport.docx`
     - Content: `@{body('HTTP')}`

**Flow Diagram**:
```
Email Arrives
    ↓
Has Attachment?
    ↓ Yes
For Each Attachment
    ↓
Is .txt file?
    ↓ Yes
HTTP POST to API
    ↓
Receive .docx
    ↓
Send Email with Report
```

---

#### Flow 2: SharePoint Folder Monitor

**Trigger**: When a file is created in a folder

**Steps**:

1. **Trigger: When a file is created (properties only)**
   - Site Address: Your SharePoint site
   - Library Name: Documents
   - Folder: /Transcripts

2. **Get file content**
   - Site Address: Same as trigger
   - File Identifier: `triggerOutputs()?['body/{Identifier}']`

3. **HTTP: Generate report**
   - Method: POST
   - URI: `https://your-app.onrender.com/generate-report-from-text`
   - Headers:
     ```json
     {
       "Content-Type": "application/json"
     }
     ```
   - Body:
     ```json
     {
       "transcript_text": "@{body('Get_file_content')}",
       "last_name": "@{triggerOutputs()?['body/{FilenameWithExtension}']}"
     }
     ```

4. **Create file**
   - Site Address: Same as trigger
   - Folder Path: /Reports
   - File Name: `PreWalk_@{triggerOutputs()?['body/{FilenameWithExtension}']}.docx`
   - File Content: `@{body('HTTP')}`

5. **Send notification email**
   - To: Team email
   - Subject: `New Report Generated`
   - Body: `Report saved to SharePoint: @{outputs('Create_file')?['body/{Link}']}`

---

#### Flow 3: Batch Processing with Recurrence

**Trigger**: Recurrence (Daily at 9 AM)

**Steps**:

1. **Trigger: Recurrence**
   - Interval: 1
   - Frequency: Day
   - Time: 09:00

2. **List files in folder**
   - Site Address: SharePoint site
   - Library: Documents
   - Folder: /Transcripts/Pending

3. **Apply to each: Process files**
   - Select output: `value` from List files

4. **Get file content**
   - File Identifier: `items('Apply_to_each')?['{Identifier}']`

5. **HTTP: Generate report**
   - Method: POST
   - URI: `https://your-app.onrender.com/generate-report-from-text`
   - Body: (same as previous flows)

6. **Create file in Reports folder**
   - Folder Path: /Reports
   - File Name: Generated report name
   - File Content: API response

7. **Move file to Processed folder**
   - Current folder: /Transcripts/Pending
   - Destination: /Transcripts/Processed

8. **Send summary email**
   - To: Admin
   - Subject: `Daily Report Generation Complete`
   - Body: `Processed @{length(body('List_files_in_folder')?['value'])} transcripts`

---

### Power Automate Connector Configuration

#### Custom Connector Setup

1. **Create Custom Connector**
   - Name: Pre-Walkthrough Report Generator
   - Host: `your-app.onrender.com`
   - Base URL: `/`

2. **Security**
   - Authentication type: No authentication (or API Key if implemented)

3. **Definition**

**Action: Generate Report from Text**
```yaml
operationId: generateReportFromText
summary: Generate Pre-Walkthrough Report
description: Generates a comprehensive report from transcript text
visibility: important

request:
  method: POST
  path: /generate-report-from-text
  headers:
    - name: Content-Type
      value: application/json
  body:
    schema:
      type: object
      properties:
        transcript_text:
          type: string
          description: Full transcript text
          required: true
        address:
          type: string
          description: Property address
        last_name:
          type: string
          description: Client last name

response:
  schema:
    type: file
    format: binary
```

4. **Test the connector**
   - Use sample transcript
   - Verify .docx file is returned

---

### Advanced Power Automate Scenarios

#### Scenario 1: Multi-Language Support

```
Trigger: Email arrives
    ↓
Detect language (Azure Cognitive Services)
    ↓
Translate to English if needed
    ↓
Generate report
    ↓
Translate report back to original language
    ↓
Send email
```

#### Scenario 2: Quality Assurance Workflow

```
Generate report
    ↓
Save to SharePoint
    ↓
Create approval request
    ↓
If approved → Send to client
    ↓
If rejected → Send back for revision
```

#### Scenario 3: CRM Integration

```
Opportunity stage changes to "Site Visit Completed"
    ↓
Retrieve transcript from CRM notes
    ↓
Generate report
    ↓
Attach report to CRM record
    ↓
Update opportunity stage to "Report Sent"
    ↓
Send notification to sales rep
```

---

### Error Handling in Power Automate

**Configure run after settings**:

```
HTTP Action
    ↓
Configure run after: is successful
    ↓
Success Path: Create file
    ↓
Configure run after: has failed
    ↓
Failure Path: Send error notification
```

**Error notification template**:
```
Subject: Report Generation Failed
Body:
Error occurred while generating report for @{triggerOutputs()?['body/subject']}

Error Details:
@{body('HTTP')?['detail']}

Timestamp: @{utcNow()}
```

---

### Performance Optimization

**Best Practices**:

1. **Batch Processing**
   - Process multiple transcripts in parallel
   - Use `Apply to each` with concurrency control (set to 5-10)

2. **Caching**
   - Store frequently accessed property data in SharePoint list
   - Check cache before API call

3. **Retry Logic**
   - Configure retry policy on HTTP action
   - Exponential backoff: 4 retries with PT10S, PT20S, PT40S, PT80S intervals

4. **Timeout Settings**
   - Set HTTP timeout to 5 minutes (300 seconds)
   - Handle timeout gracefully

---

### Monitoring & Logging

**Power Automate Analytics**:
- Flow run history
- Success/failure rates
- Average execution time
- Error patterns

**Custom Logging**:
```
After each HTTP call:
    ↓
Append to SharePoint list:
    - Timestamp
    - Transcript ID
    - Status (Success/Failed)
    - Processing time
    - Error message (if any)
```

---

## Deployment Guide

### Prerequisites

- Python 3.11+
- Git
- API Keys:
  - OpenAI API key
  - RapidAPI key (US Real Estate Listings)
  - SerpAPI key (optional)

---

### Local Development Setup

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/pre-walkthrough-report-generator.git
cd pre-walkthrough-report-generator
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required
OPENAI_API_KEY=sk-your-openai-key-here
RAPIDAPI_KEY=your-rapidapi-key-here

# Optional
SERPAPI_KEY=your-serpapi-key-here
PORT=8000
LOG_LEVEL=INFO
```

#### 5. Create Required Directories

```bash
mkdir -p data/transcripts
mkdir -p templates
```

#### 6. Add Header/Footer Images

Place `header.png` and `footer.png` in the root directory.

#### 7. Run Development Server

```bash
# Using uvicorn directly
uvicorn fastapi_server:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python fastapi_server.py
```

#### 8. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Test report generation
curl -X POST http://localhost:8000/generate-report-from-text \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "Test transcript content...",
    "address": "123 Main St, Brooklyn, NY",
    "last_name": "Test"
  }' \
  --output test_report.docx
```

---

### Production Deployment

#### Option 1: Render (Recommended)

**Step 1: Prepare Repository**

Ensure these files exist:
- `requirements.txt`
- `render.yaml`
- `app.py` (ASGI entry point)

**Step 2: Create Render Account**

1. Go to https://render.com
2. Sign up with GitHub account
3. Authorize Render to access your repositories

**Step 3: Create New Web Service**

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure service:
   - **Name**: `prewalk-generator`
   - **Environment**: `Python 3`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Build Command**:
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt && mkdir -p data templates
     ```
   - **Start Command**:
     ```bash
     gunicorn app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 1 --timeout 120
     ```

**Step 4: Add Environment Variables**

In Render dashboard, add:
```
OPENAI_API_KEY=sk-your-key
RAPIDAPI_KEY=your-key
SERPAPI_KEY=your-key (optional)
PYTHON_VERSION=3.11.0
```

**Step 5: Deploy**

1. Click "Create Web Service"
2. Wait for build to complete (~5 minutes)
3. Test your deployment: `https://your-app.onrender.com/health`

**Step 6: Configure Custom Domain (Optional)**

1. Go to Settings → Custom Domain
2. Add your domain
3. Update DNS records as instructed

**Render Configuration File** (`render.yaml`):

```yaml
services:
  - type: web
    name: prewalk-generator
    env: python
    buildCommand: pip install --upgrade pip && pip install -r requirements.txt && mkdir -p data templates
    startCommand: gunicorn app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 1 --timeout 120
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: OPENAI_API_KEY
        sync: false
      - key: RAPIDAPI_KEY
        sync: false
    healthCheckPath: /health
    autoDeploy: true
```

---

#### Option 2: Railway

**Step 1: Install Railway CLI**

```bash
npm install -g @railway/cli
```

**Step 2: Login**

```bash
railway login
```

**Step 3: Initialize Project**

```bash
railway init
```

**Step 4: Add Environment Variables**

```bash
railway variables set OPENAI_API_KEY=sk-your-key
railway variables set RAPIDAPI_KEY=your-key
```

**Step 5: Deploy**

```bash
railway up
```

**Railway Configuration** (`railway.json`):

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

#### Option 3: Fly.io

**Step 1: Install Fly CLI**

```bash
curl -L https://fly.io/install.sh | sh
```

**Step 2: Login**

```bash
fly auth login
```

**Step 3: Launch App**

```bash
fly launch
```

**Step 4: Set Secrets**

```bash
fly secrets set OPENAI_API_KEY=sk-your-key
fly secrets set RAPIDAPI_KEY=your-key
```

**Step 5: Deploy**

```bash
fly deploy
```

**Fly Configuration** (`fly.toml`):

```toml
app = "prewalk-generator"
primary_region = "ewr"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[services]]
  protocol = "tcp"
  internal_port = 8080

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [services.concurrency]
    type = "connections"
    hard_limit = 25
    soft_limit = 20

[[services.tcp_checks]]
  interval = "15s"
  timeout = "2s"
  grace_period = "5s"
```

---

#### Option 4: Azure Functions (Serverless)

**Step 1: Install Azure Functions Core Tools**

```bash
npm install -g azure-functions-core-tools@4
```

**Step 2: Create Function App**

```bash
func init PreWalkGenerator --python
cd PreWalkGenerator
func new --name GenerateReport --template "HTTP trigger"
```

**Step 3: Update `function_app.py`**

```python
import azure.functions as func
import logging
from fastapi_server import process_transcript_and_generate_report
import tempfile
import os

app = func.FunctionApp()

@app.function_name(name="GenerateReport")
@app.route(route="generate-report", methods=["POST"])
def generate_report(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Get transcript from request
        transcript_text = req.get_json().get('transcript_text')
        address = req.get_json().get('address')
        last_name = req.get_json().get('last_name')
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w') as f:
            f.write(transcript_text)
            temp_path = f.name
        
        # Generate report
        report_path = process_transcript_and_generate_report(
            temp_path, address, last_name
        )
        
        # Read and return report
        with open(report_path, 'rb') as f:
            report_data = f.read()
        
        # Cleanup
        os.unlink(temp_path)
        os.unlink(report_path)
        
        return func.HttpResponse(
            report_data,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
```

**Step 4: Deploy to Azure**

```bash
az login
az functionapp create --resource-group MyResourceGroup \
  --consumption-plan-location eastus \
  --runtime python --runtime-version 3.11 \
  --functions-version 4 \
  --name prewalk-generator --storage-account mystorageaccount

func azure functionapp publish prewalk-generator
```

---

### Docker Deployment

**Dockerfile**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data templates

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "app:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "120"]
```

**Build and Run**:

```bash
# Build image
docker build -t prewalk-generator .

# Run container
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  -e RAPIDAPI_KEY=your-key \
  --name prewalk-generator \
  prewalk-generator

# Check logs
docker logs prewalk-generator

# Stop container
docker stop prewalk-generator
```

**Docker Compose** (`docker-compose.yml`):

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - RAPIDAPI_KEY=${RAPIDAPI_KEY}
      - SERPAPI_KEY=${SERPAPI_KEY}
    volumes:
      - ./data:/app/data
      - ./templates:/app/templates
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run with:
```bash
docker-compose up -d
```

---

### CI/CD Pipeline

#### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=pre_walkthrough_generator --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to Render
      uses: johnbeynon/render-deploy-action@v0.0.8
      with:
        service-id: ${{ secrets.RENDER_SERVICE_ID }}
        api-key: ${{ secrets.RENDER_API_KEY }}
```

---

### Monitoring & Logging

#### Application Logging

**Configure structured logging**:

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Configure logger
handler = logging.FileHandler('app.log')
handler.setFormatter(JSONFormatter())
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

#### Health Monitoring

**Uptime Monitoring Services**:
- **UptimeRobot**: Free tier, 5-minute checks
- **Pingdom**: Comprehensive monitoring
- **StatusCake**: Free tier available

**Setup**:
1. Add `/health` endpoint to monitoring
2. Set check interval: 5 minutes
3. Configure alerts (email, SMS, Slack)
4. Set up status page

#### Performance Monitoring

**New Relic Integration**:

```python
# Install: pip install newrelic

# newrelic.ini configuration
[newrelic]
license_key = YOUR_LICENSE_KEY
app_name = Pre-Walkthrough Generator
monitor_mode = true
log_level = info

# Wrap application
import newrelic.agent
newrelic.agent.initialize('newrelic.ini')

@newrelic.agent.background_task()
def process_transcript_and_generate_report(...):
    ...
```

**Sentry Error Tracking**:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
    environment="production"
)
```

---

### Scaling Considerations

#### Horizontal Scaling

**Render Auto-Scaling**:
```yaml
services:
  - type: web
    name: prewalk-generator
    scaling:
      minInstances: 1
      maxInstances: 10
      targetMemoryPercent: 80
      targetCPUPercent: 80
```

#### Database for Caching

**Redis Integration** (for property data caching):

```python
import redis
import json

redis_client = redis.Redis(
    host='your-redis-host',
    port=6379,
    password='your-password',
    decode_responses=True
)

def get_property_details_cached(property_id: str):
    # Check cache first
    cache_key = f"property:{property_id}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Fetch from API
    details = get_property_details(property_id)
    
    # Cache for 24 hours
    redis_client.setex(cache_key, 86400, json.dumps(details))
    
    return details
```

#### Queue System

**Celery for Background Processing**:

```python
from celery import Celery

celery_app = Celery(
    'prewalk_generator',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@celery_app.task
def generate_report_async(transcript_text, address, last_name):
    return process_transcript_and_generate_report(
        transcript_text, address, last_name
    )

# In FastAPI endpoint
@app.post("/generate-report-async")
async def generate_report_async_endpoint(request: TranscriptRequest):
    task = generate_report_async.delay(
        request.transcript_text,
        request.address,
        request.last_name
    )
    return {"task_id": task.id, "status": "processing"}

@app.get("/report-status/{task_id}")
async def get_report_status(task_id: str):
    task = generate_report_async.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }
```

---

### Backup & Disaster Recovery

#### Data Backup Strategy

**Automated Backups**:

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup data directory
tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" data/

# Backup configuration
cp config.json "$BACKUP_DIR/config_$DATE.json"

# Upload to S3
aws s3 cp "$BACKUP_DIR/data_$DATE.tar.gz" s3://your-bucket/backups/

# Cleanup old backups (keep last 30 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

**Cron Schedule**:
```cron
0 2 * * * /path/to/backup.sh
```

#### Disaster Recovery Plan

1. **Service Outage**:
   - Render auto-restarts failed services
   - Health checks trigger alerts
   - Fallback to backup deployment

2. **Data Loss**:
   - Restore from S3 backups
   - Replay failed requests from logs

3. **API Key Compromise**:
   - Rotate keys immediately
   - Update environment variables
   - Audit access logs

---

### Security Hardening

#### API Key Security

**Environment Variables Only**:
```python
# Never commit API keys
# Use environment variables
import os

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set")
```

#### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/generate-report")
@limiter.limit("10/minute")
async def generate_report(request: Request, ...):
    ...
```

#### Input Validation

```python
from pydantic import BaseModel, validator, Field

class TranscriptRequest(BaseModel):
    transcript_text: str = Field(..., min_length=50, max_length=100000)
    address: Optional[str] = Field(None, max_length=200)
    last_name: Optional[str] = Field(None, max_length=50)
    
    @validator('transcript_text')
    def validate_transcript(cls, v):
        if not v.strip():
            raise ValueError('Transcript cannot be empty')
        return v
```

#### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

#### HTTPS Enforcement

```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Redirect HTTP to HTTPS
app.add_middleware(HTTPSRedirectMiddleware)
```

---

## Configuration Management

### Environment Variables

**Required Variables**:

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o | `sk-proj-...` | Yes |
| `RAPIDAPI_KEY` | RapidAPI key for property data | `abc123...` | Yes |
| `SERPAPI_KEY` | SerpAPI key for Google search | `xyz789...` | No |
| `PORT` | Server port | `8000` | No (default: 8000) |
| `LOG_LEVEL` | Logging level | `INFO` | No (default: INFO) |
| `PYTHON_VERSION` | Python version | `3.11.0` | No (deployment) |

### Configuration Files

#### 1. `config.json`

Runtime configuration for local development:

```json
{
  "rapidapi_key": "your-rapidapi-key",
  "openai_api_key": "sk-your-openai-key",
  "serpapi_key": "your-serpapi-key",
  "api_host": "us-real-estate-listings.p.rapidapi.com"
}
```

**Location**: `pre_walkthrough_generator/config.json`

**Priority**: Environment variables override config.json values

#### 2. `.env` File

Environment variables for local development:

```env
# API Keys
OPENAI_API_KEY=sk-your-openai-key-here
RAPIDAPI_KEY=your-rapidapi-key-here
SERPAPI_KEY=your-serpapi-key-here

# Server Configuration
PORT=8000
LOG_LEVEL=INFO
WORKERS=1
TIMEOUT=120

# Feature Flags
ENABLE_CACHING=false
ENABLE_METRICS=true
```

**Location**: Root directory (`.env`)

**Note**: Never commit `.env` to version control

#### 3. `render.yaml`

Render deployment configuration:

```yaml
services:
  - type: web
    name: prewalk-generator
    env: python
    buildCommand: |
      pip install --upgrade pip && 
      pip install -r requirements.txt && 
      mkdir -p data templates
    startCommand: |
      gunicorn app:app 
      -k uvicorn.workers.UvicornWorker 
      --bind 0.0.0.0:$PORT 
      --workers 1 
      --timeout 120
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: OPENAI_API_KEY
        sync: false
      - key: RAPIDAPI_KEY
        sync: false
    healthCheckPath: /health
    autoDeploy: true
```

### Dynamic Configuration Updates

**Update API keys without restart**:

```bash
# Via API
curl -X PUT https://your-app.onrender.com/config/api-keys \
  -d "openai_key=sk-new-key" \
  -d "rapidapi_key=new-rapid-key"

# Via Python
import requests

requests.put(
    "https://your-app.onrender.com/config/api-keys",
    data={
        "openai_key": "sk-new-key",
        "rapidapi_key": "new-rapid-key"
    }
)
```

**Reload configuration**:

```bash
curl -X POST https://your-app.onrender.com/config/reload
```

### Configuration Best Practices

1. **Never commit secrets**: Use `.gitignore` for `.env` and `config.json`
2. **Use environment variables in production**: More secure than config files
3. **Rotate API keys regularly**: Every 90 days minimum
4. **Use different keys per environment**: Dev, staging, production
5. **Monitor API usage**: Set up alerts for unusual activity
6. **Document all variables**: Keep this documentation updated

---

## Data Flow & Processing Pipeline

### Complete Request Flow

```
1. REQUEST RECEPTION
   ├─ HTTP POST to /generate-report-from-text
   ├─ FastAPI receives JSON payload
   ├─ Pydantic validates request schema
   └─ Extract: transcript_text, address, last_name

2. TRANSCRIPT PROCESSING
   ├─ Clean transcript (remove timestamps, formatting)
   ├─ Send to OpenAI GPT-4o
   │  ├─ Model: gpt-4o
   │  ├─ Temperature: 0 (deterministic)
   │  ├─ Max tokens: 4000
   │  └─ Response format: JSON
   ├─ Parse structured JSON response
   └─ Extract:
      ├─ Property info (address, building type)
      ├─ Client info (names, preferences, red flags)
      ├─ Renovation scope (kitchen, bathrooms, additional)
      ├─ Timeline (duration, phasing, key dates)
      ├─ Materials & design preferences
      └─ Project management details

3. ADDRESS RESOLUTION
   ├─ Use provided address OR
   ├─ Extract from transcript_info OR
   ├─ Parse from transcript text OR
   └─ Fallback to filename + "Brooklyn, NY"
   
   ├─ Clean address:
   │  ├─ Standardize abbreviations
   │  ├─ Remove extra whitespace
   │  └─ Format apartment numbers
   └─ Validate format

4. PROPERTY ID LOOKUP
   ├─ DuckDuckGo Search (Primary)
   │  ├─ Query: "{address} site:realtor.com"
   │  ├─ Parse HTML results
   │  ├─ Extract property ID from URL
   │  └─ Retry with variations if needed
   │
   ├─ Realtor.com Site Search (Fallback)
   │  ├─ Direct search on Realtor.com
   │  ├─ Parse search results page
   │  └─ Extract first matching listing
   │
   └─ SerpAPI (Optional)
      ├─ Google search via API
      └─ More reliable but costs money

5. PROPERTY DATA ENRICHMENT
   ├─ RapidAPI: /v2/property
   │  ├─ Input: property_id
   │  ├─ Output: Property details
   │  └─ Extract:
   │     ├─ Price (current & last sold)
   │     ├─ Bedrooms, bathrooms, sqft
   │     ├─ Year built, property type
   │     ├─ HOA fees, neighborhood
   │     └─ Listing URL (if available)
   │
   └─ RapidAPI: /propertyPhotos
      ├─ Input: property_id
      ├─ Output: Images array
      └─ Separate:
         ├─ Property photos
         └─ Floor plans (by tag)

6. URL CONSTRUCTION
   ├─ Check if API provided URL
   ├─ If not, build canonical URL:
   │  ├─ Slugify address components
   │  ├─ Format: {street}_{city}_{state}_{zip}_M{property_id}
   │  └─ Example: 123-Main-St_Brooklyn_NY_11201_M12345678
   └─ Validate URL format

7. DATA ASSEMBLY
   └─ Create final_data dictionary:
      ├─ property_address
      ├─ property_id
      ├─ realtor_url
      ├─ property_details (from API)
      ├─ images (property photos)
      ├─ floor_plans (separated)
      └─ transcript_info (from GPT-4o)

8. DOCUMENT GENERATION
   ├─ Initialize Word document
   ├─ Add header image (0.8" height)
   ├─ Add title & address
   ├─ Generate sections:
   │  ├─ Executive Summary
   │  │  ├─ Project goals
   │  │  ├─ Client drivers
   │  │  └─ Key numbers (budget + timeline)
   │  │
   │  ├─ Property Details Table
   │  │  ├─ Price, sqft, bed/bath
   │  │  ├─ Year built, type, HOA
   │  │  └─ Neighborhood
   │  │
   │  ├─ Client Details Table
   │  │  ├─ Names, contact, profession
   │  │  ├─ Preferences
   │  │  └─ Red flags
   │  │
   │  ├─ Property Links
   │  │  └─ Realtor.com hyperlink
   │  │
   │  ├─ Floor Plans
   │  │  ├─ Download images
   │  │  ├─ Convert to PNG if needed
   │  │  ├─ Embed at 6" width
   │  │  └─ Add image URL link
   │  │
   │  ├─ Building Requirements
   │  │  └─ Dynamic rules from transcript
   │  │
   │  ├─ Renovation Scope
   │  │  ├─ Kitchen table
   │  │  ├─ Bathrooms table
   │  │  └─ Additional work table
   │  │
   │  ├─ Timeline & Phasing Table
   │  │  ├─ Duration, phasing
   │  │  └─ Living arrangements
   │  │
   │  ├─ Budget Summary Table
   │  │  ├─ Kitchen costs
   │  │  ├─ Bathroom costs
   │  │  ├─ Additional costs
   │  │  └─ Total range
   │  │
   │  └─ Notes
   │     ├─ Material sourcing
   │     ├─ Special requirements
   │     └─ Communication preferences
   │
   ├─ Add footer image (0.8" height)
   └─ Save document

9. RESPONSE DELIVERY
   ├─ Save .docx to data/ directory
   ├─ Generate filename: PreWalk_{address/lastname}.docx
   ├─ Return FileResponse
   │  ├─ Content-Type: application/vnd...wordprocessingml.document
   │  ├─ Filename: PreWalkReport_{lastname}.docx
   │  └─ Binary content
   └─ Client downloads file

10. CLEANUP & LOGGING
    ├─ Delete temporary files
    ├─ Log request metrics
    ├─ Update server statistics
    └─ Return success/error status
```

### Processing Time Breakdown

| Stage | Average Time | Notes |
|-------|--------------|-------|
| Request validation | <0.1s | Pydantic validation |
| Transcript processing (GPT-4o) | 5-15s | Depends on transcript length |
| Address resolution | <1s | Regex + cleaning |
| Property ID lookup | 2-5s | Web scraping |
| Property details API | 1-2s | RapidAPI call |
| Property photos API | 1-2s | RapidAPI call |
| Image download | 2-5s | Per image |
| Document generation | 2-5s | Word assembly |
| **Total** | **15-35s** | End-to-end |

### Error Handling Flow

```
Error Occurs
    ↓
Catch Exception
    ↓
Log Error Details
    ├─ Timestamp
    ├─ Error type
    ├─ Stack trace
    └─ Request context
    ↓
Determine Error Type
    ├─ Validation Error (400)
    ├─ External API Error (503)
    ├─ Processing Error (500)
    └─ Timeout Error (504)
    ↓
Return Error Response
    ├─ HTTP status code
    ├─ Error message
    └─ Request ID
    ↓
Cleanup Resources
    ├─ Delete temp files
    └─ Close connections
    ↓
Update Error Metrics
```

---

## Security & Best Practices

### API Key Management

#### Storage
- **Never commit API keys to Git**
- Use environment variables in production
- Use `.env` files for local development (add to `.gitignore`)
- Use secrets management services (AWS Secrets Manager, Azure Key Vault)

#### Rotation
```bash
# Rotate keys every 90 days
# 1. Generate new key
# 2. Update environment variable
# 3. Test with new key
# 4. Revoke old key
# 5. Monitor for errors
```

#### Access Control
- Limit API key permissions to minimum required
- Use separate keys for dev/staging/production
- Monitor API usage for anomalies
- Set up billing alerts

### Input Validation

**Transcript Validation**:
```python
def validate_transcript(transcript: str) -> bool:
    # Check minimum length
    if len(transcript.strip()) < 50:
        raise ValueError("Transcript too short")
    
    # Check maximum length
    if len(transcript) > 100000:
        raise ValueError("Transcript too long")
    
    # Check for meaningful content
    meaningful = re.sub(r'[{}":\s\n\r]', '', transcript)
    if len(meaningful) < 50:
        raise ValueError("Insufficient content")
    
    return True
```

**Address Validation**:
```python
def validate_address(address: str) -> bool:
    # Check format
    if not re.match(r'\d+\s+\w+', address):
        raise ValueError("Invalid address format")
    
    # Check length
    if len(address) > 200:
        raise ValueError("Address too long")
    
    return True
```

### Rate Limiting

**Implementation**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/generate-report")
@limiter.limit("10/minute")
async def generate_report(request: Request, ...):
    ...
```

**Recommended Limits**:
- Public API: 10 requests/minute per IP
- Authenticated API: 100 requests/minute per user
- Burst allowance: 20 requests

### Data Privacy

**PII Handling**:
- Don't log sensitive information (names, addresses, phone numbers)
- Sanitize logs before storage
- Implement data retention policies
- Comply with GDPR/CCPA requirements

**Example Sanitization**:
```python
import re

def sanitize_log(text: str) -> str:
    # Remove phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    
    # Remove email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Remove addresses
    text = re.sub(r'\b\d+\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd)\b', '[ADDRESS]', text)
    
    return text
```

### HTTPS/TLS

**Enforce HTTPS**:
```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
```

**Certificate Management**:
- Use Let's Encrypt for free SSL certificates
- Auto-renewal with certbot
- Monitor certificate expiration

### CORS Configuration

**Restrictive CORS**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "Authorization"],
)
```

### Error Handling Best Practices

**Don't expose internal details**:
```python
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log full error internally
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Return generic message to client
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )
```

### Dependency Security

**Regular Updates**:
```bash
# Check for vulnerabilities
pip install safety
safety check

# Update dependencies
pip list --outdated
pip install --upgrade package-name
```

**Automated Scanning**:
```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Snyk
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

### Logging Best Practices

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "report_generated",
    request_id=request_id,
    address=sanitize_address(address),
    processing_time=elapsed_time,
    success=True
)
```

**Log Levels**:
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potentially harmful situations
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical messages for very serious errors

### Backup & Recovery

**Automated Backups**:
```bash
#!/bin/bash
# Daily backup script

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups"

# Backup data
tar -czf "$BACKUP_DIR/data_$DATE.tar.gz" data/

# Upload to S3
aws s3 cp "$BACKUP_DIR/data_$DATE.tar.gz" s3://your-bucket/backups/

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

**Recovery Procedure**:
1. Identify backup to restore
2. Download from S3
3. Extract to data directory
4. Verify integrity
5. Restart service

---

## Troubleshooting

### Common Issues

#### 1. "OpenAI API Error: Rate Limit Exceeded"

**Cause**: Too many requests to OpenAI API

**Solution**:
```python
# Implement exponential backoff
import time
from openai import RateLimitError

def call_openai_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(...)
        except RateLimitError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                raise
```

#### 2. "Property ID Not Found"

**Cause**: Web scraping failed or property not on Realtor.com

**Solution**:
- Verify address format is correct
- Check if property exists on Realtor.com manually
- Try alternative search queries
- Use SerpAPI as fallback

**Debug**:
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check search results
property_id = property_api.get_property_id(address)
print(f"Property ID: {property_id}")
```

#### 3. "Image Download Failed"

**Cause**: Image URL invalid or server timeout

**Solution**:
```python
def download_image_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return BytesIO(response.content)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                logger.error(f"Failed to download image: {url}")
                return None
```

#### 4. "Document Generation Error"

**Cause**: Invalid data structure or missing template

**Solution**:
- Verify all required fields are present
- Check template file exists
- Validate data types

**Debug**:
```python
# Print data structure
import json
print(json.dumps(final_data, indent=2, default=str))

# Validate required fields
required_fields = ['property_address', 'property_details', 'transcript_info']
for field in required_fields:
    if field not in final_data:
        raise ValueError(f"Missing required field: {field}")
```

#### 5. "Deployment Failed on Render"

**Cause**: Build command error or missing dependencies

**Solution**:
1. Check build logs in Render dashboard
2. Verify `requirements.txt` is complete
3. Test build locally:
   ```bash
   pip install -r requirements.txt
   ```
4. Check Python version matches (3.11+)

#### 6. "Timeout Error"

**Cause**: Request taking too long (>120 seconds)

**Solution**:
- Increase timeout in gunicorn config:
  ```bash
  gunicorn app:app --timeout 300
  ```
- Optimize processing:
  - Cache property data
  - Reduce image sizes
  - Use async operations

#### 7. "BeautifulSoup4 Not Found"

**Cause**: Optional dependency not installed

**Solution**:
```bash
pip install beautifulsoup4 lxml soupsieve
```

**Verify**:
```python
try:
    from bs4 import BeautifulSoup
    print("BeautifulSoup4 installed successfully")
except ImportError:
    print("BeautifulSoup4 not available")
```

### Debugging Tools

#### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
```

#### Test Individual Components

```python
# Test transcript processor
from pre_walkthrough_generator.src.transcript_processor import TranscriptProcessor

processor = TranscriptProcessor(openai_api_key)
result = processor.extract_info("test transcript")
print(json.dumps(result, indent=2))

# Test property API
from pre_walkthrough_generator.src.property_api import PropertyAPI

api = PropertyAPI(rapidapi_key, openai_api_key)
property_id = api.get_property_id("123 Main St, Brooklyn, NY")
print(f"Property ID: {property_id}")

details = api.get_property_details(property_id)
print(json.dumps(details, indent=2))
```

#### Monitor API Calls

```python
import time

class APIMonitor:
    def __init__(self):
        self.calls = []
    
    def log_call(self, api_name, duration, success):
        self.calls.append({
            'api': api_name,
            'duration': duration,
            'success': success,
            'timestamp': time.time()
        })
    
    def get_stats(self):
        total = len(self.calls)
        successful = sum(1 for c in self.calls if c['success'])
        avg_duration = sum(c['duration'] for c in self.calls) / total if total > 0 else 0
        
        return {
            'total_calls': total,
            'successful': successful,
            'failed': total - successful,
            'avg_duration': avg_duration
        }

monitor = APIMonitor()

# Wrap API calls
start = time.time()
try:
    result = api.get_property_details(property_id)
    monitor.log_call('get_property_details', time.time() - start, True)
except Exception:
    monitor.log_call('get_property_details', time.time() - start, False)
```

### Performance Optimization

#### 1. Caching Strategy

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def get_property_details_cached(property_id: str):
    return get_property_details(property_id)

# Redis caching
def get_cached_or_fetch(key, fetch_func, ttl=3600):
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    
    data = fetch_func()
    redis_client.setex(key, ttl, json.dumps(data))
    return data
```

#### 2. Async Operations

```python
import asyncio
import aiohttp

async def fetch_property_data_async(property_id):
    async with aiohttp.ClientSession() as session:
        # Fetch details and photos in parallel
        details_task = fetch_details(session, property_id)
        photos_task = fetch_photos(session, property_id)
        
        details, photos = await asyncio.gather(details_task, photos_task)
        
        return {'details': details, 'photos': photos}
```

#### 3. Image Optimization

```python
from PIL import Image

def optimize_image(image_bytes, max_width=800):
    img = Image.open(BytesIO(image_bytes))
    
    # Resize if too large
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)
    
    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Save optimized
    output = BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    output.seek(0)
    
    return output
```

---

## Appendices

### Appendix A: API Response Examples

#### OpenAI GPT-4o Response

```json
{
  "property_address": "268 Babbitt Road #M7, Bedford, NY 10507",
  "property_info": {
    "building_type": "condo",
    "total_units": null,
    "year_built": null,
    "building_rules": [
      "No structural changes without board approval",
      "Quiet hours 10 PM - 8 AM"
    ],
    "building_features": ["Elevator", "Parking garage"]
  },
  "client_info": {
    "names": ["John Smith", "Jane Smith"],
    "phone": "(555) 123-4567",
    "profession": "Software Engineer",
    "preferences": {
      "budget_sensitivity": "medium",
      "decision_making": "moderate",
      "design_involvement": "high",
      "quality_preference": "mid-range"
    },
    "constraints": [
      "Must complete before school year starts",
      "Working from home, need quiet workspace"
    ],
    "red_flags": {
      "is_negative_reviewer": false,
      "payment_concerns": false,
      "unrealistic_expectations": false,
      "communication_issues": false
    }
  },
  "renovation_scope": {
    "kitchen": {
      "description": "Full kitchen renovation with new cabinets and appliances",
      "estimated_cost": {
        "range": {"min": 50000, "max": 75000}
      },
      "plumbing_changes": "Relocate sink to island",
      "electrical_changes": "Add under-cabinet lighting and new outlets",
      "specific_requirements": [
        "Quartz countertops",
        "Soft-close cabinets",
        "Induction cooktop"
      ],
      "appliances": [
        "Refrigerator",
        "Dishwasher",
        "Range",
        "Microwave"
      ],
      "cabinets_and_countertops": {
        "type": "Custom shaker-style cabinets",
        "preferences": ["White cabinets", "Quartz countertops"]
      }
    },
    "bathrooms": {
      "count": 2,
      "cost_per_bathroom": 25000,
      "plumbing_changes": "Replace all fixtures",
      "specific_requirements": [
        "Walk-in shower in master",
        "Double vanity"
      ],
      "fixtures": ["Toilet", "Sink", "Shower", "Bathtub"],
      "finishes": ["Porcelain tile", "Chrome fixtures"]
    },
    "additional_work": {
      "rooms": ["Living room flooring", "Bedroom painting"],
      "structural_changes": [],
      "systems_updates": ["HVAC upgrade"],
      "custom_features": ["Built-in bookshelf"],
      "estimated_costs": {
        "per_sqft_cost": null,
        "total_estimated_range": {"min": 100000, "max": 150000},
        "architect_fees": {"percentage": 10, "estimated_amount": 12000},
        "additional_fees": ["Permit fees: $2,000"]
      }
    },
    "timeline": {
      "total_duration": "3-4 months",
      "phasing": "Kitchen first, then bathrooms",
      "living_arrangements": "Will stay in home during renovation",
      "constraints": ["Must complete by August 15"],
      "key_dates": {
        "survey_completion": "June 1, 2025",
        "walkthrough_scheduled": "June 15, 2025",
        "project_start": "July 1, 2025",
        "other_milestones": ["Kitchen completion: July 31"]
      }
    }
  },
  "materials_and_design": {
    "sourcing_responsibility": "Contractor will source all materials",
    "specific_materials": ["Quartz countertops", "Porcelain tile"],
    "style_preferences": ["Modern", "Minimalist"],
    "quality_preferences": ["Mid-range to high-end"],
    "trade_discounts": ["10% discount on appliances"],
    "reuse_materials": []
  },
  "project_management": {
    "client_involvement": "Weekly progress meetings",
    "design_services": ["3D renderings", "Material selection"],
    "documentation_needs": ["Building permits", "Architectural drawings"],
    "permit_requirements": ["Kitchen permit", "Plumbing permit"],
    "contractor_requirements": ["Licensed", "Insured", "References"],
    "communication_preferences": "Email and text",
    "decision_process": "Joint decisions with spouse",
    "company_details": {
      "company_name": "ABC Renovations",
      "contact_person": "Mike Johnson",
      "services_offered": ["Design", "Construction", "Project management"],
      "fees_structure": ["10% management fee", "Cost-plus pricing"],
      "process_description": "Design phase, approval, construction, final walkthrough"
    }
  }
}
```

#### RapidAPI Property Details Response

```json
{
  "data": {
    "property_id": "M12345678",
    "list_price": 450000,
    "last_sold_price": 420000,
    "last_sold_date": "2023-05-15",
    "location": {
      "address": {
        "line": "123 Main Street",
        "street_number": "123",
        "street_name": "Main",
        "street_suffix": "St",
        "city": "Brooklyn",
        "state_code": "NY",
        "state": "New York",
        "postal_code": "11201"
      },
      "neighborhoods": [
        {"name": "Brooklyn Heights"}
      ]
    },
    "description": {
      "beds": 2,
      "baths": 2,
      "sqft": 1200,
      "type": "condo",
      "sub_type": "condo",
      "year_built": 2015
    },
    "hoa": {
      "fee": 450
    },
    "photos": [
      {
        "href": "https://example.com/photo1.jpg",
        "tags": [{"label": "kitchen"}]
      },
      {
        "href": "https://example.com/floorplan.jpg",
        "tags": [{"label": "floor_plan"}]
      }
    ],
    "details": [
      {
        "category": "Bedrooms",
        "text": ["Bedrooms: 2"]
      },
      {
        "category": "Bathrooms",
        "text": ["Bathrooms: 2"]
      }
    ]
  }
}
```

### Appendix B: Sample Transcripts

#### Example 1: Kitchen Renovation

```
We visited the property at 123 Main Street, Brooklyn, NY 11201 today. The clients, John and Jane Smith, are looking to do a full kitchen renovation. They mentioned a budget of $50,000 to $75,000.

Key requirements:
- New cabinets (white shaker style)
- Quartz countertops
- Induction cooktop
- Under-cabinet lighting
- Relocate sink to island

Timeline: They want to complete the project in 3-4 months, starting in July. They'll be staying in the home during renovation.

The clients are both working from home, so they need the work to be done during business hours with minimal noise disruption. They prefer email communication for updates.

Budget breakdown discussed:
- Cabinets: $15,000-$20,000
- Countertops: $8,000-$10,000
- Appliances: $10,000-$15,000
- Labor: $15,000-$20,000
- Permits and misc: $2,000-$5,000

They seem reasonable and have realistic expectations. No red flags noted.
```

#### Example 2: Whole House Renovation

```
Property: 456 Oak Avenue, Apt 3B, Brooklyn, NY 11215

Clients: Michael and Sarah Johnson
Phone: (555) 987-6543
Profession: Doctor and Teacher

Scope:
1. Kitchen - Full gut renovation
   - Budget: $80,000-$100,000
   - Custom cabinets, marble countertops
   - High-end appliances (Sub-Zero, Wolf)
   - Relocate plumbing and electrical

2. Bathrooms (2) - Complete renovation
   - Master: $40,000 (walk-in shower, double vanity)
   - Guest: $25,000 (tub/shower combo)
   - Heated floors in both

3. Additional Work:
   - Hardwood flooring throughout (1,500 sqft @ $15/sqft)
   - Paint all rooms
   - New HVAC system
   - Built-in bookshelves in living room

Total Budget: $200,000-$250,000
Timeline: 6 months
Start Date: September 1, 2025

Living Arrangements: Will move out during renovation

Special Requirements:
- Must coordinate with co-op board
- Need architect for structural changes
- Permits required for plumbing and electrical

Client Notes:
- Very detail-oriented
- Want weekly progress meetings
- Prefer high-quality materials
- Have done renovations before
- Good communication, responsive

Red Flags: None
```

### Appendix C: Glossary

**API (Application Programming Interface)**: A set of protocols for building and integrating application software.

**ASGI (Asynchronous Server Gateway Interface)**: A spiritual successor to WSGI, providing a standard interface between async-capable Python web servers and applications.

**BeautifulSoup**: A Python library for parsing HTML and XML documents.

**CORS (Cross-Origin Resource Sharing)**: A mechanism that allows restricted resources on a web page to be requested from another domain.

**Docker**: A platform for developing, shipping, and running applications in containers.

**FastAPI**: A modern, fast web framework for building APIs with Python based on standard Python type hints.

**GPT-4o**: OpenAI's latest language model with improved performance and capabilities.

**Gunicorn**: A Python WSGI HTTP server for UNIX, commonly used to serve Python web applications.

**HTTPS (Hypertext Transfer Protocol Secure)**: An extension of HTTP that uses encryption for secure communication.

**JSON (JavaScript Object Notation)**: A lightweight data interchange format.

**JWT (JSON Web Token)**: A compact, URL-safe means of representing claims to be transferred between two parties.

**OAuth 2.0**: An authorization framework that enables applications to obtain limited access to user accounts.

**PaaS (Platform as a Service)**: A cloud computing model that provides a platform for customers to develop, run, and manage applications.

**Pydantic**: A data validation library using Python type annotations.

**RapidAPI**: A marketplace for APIs that provides a unified interface for accessing multiple APIs.

**Redis**: An in-memory data structure store used as a database, cache, and message broker.

**REST (Representational State Transfer)**: An architectural style for designing networked applications.

**SerpAPI**: A service that provides Google search results via API.

**SSL/TLS (Secure Sockets Layer/Transport Layer Security)**: Cryptographic protocols for secure communication.

**Uvicorn**: A lightning-fast ASGI server implementation.

**WSGI (Web Server Gateway Interface)**: A specification for a universal interface between web servers and Python web applications.

### Appendix D: Useful Commands

#### Development

```bash
# Start development server
uvicorn fastapi_server:app --reload

# Run with specific port
uvicorn fastapi_server:app --port 8080

# Run with multiple workers
gunicorn app:app -k uvicorn.workers.UvicornWorker --workers 4

# Check Python version
python --version

# List installed packages
pip list

# Check for outdated packages
pip list --outdated

# Update package
pip install --upgrade package-name

# Freeze dependencies
pip freeze > requirements.txt
```

#### Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test report generation
curl -X POST http://localhost:8000/generate-report-from-text \
  -H "Content-Type: application/json" \
  -d @test_request.json \
  --output test_report.docx

# Check API documentation
open http://localhost:8000/docs

# Run Python tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=pre_walkthrough_generator
```

#### Deployment

```bash
# Render deployment
git push origin main  # Auto-deploys

# Railway deployment
railway up

# Fly.io deployment
fly deploy

# Docker build
docker build -t prewalk-generator .

# Docker run
docker run -p 8000:8000 prewalk-generator

# Docker compose
docker-compose up -d
```

#### Monitoring

```bash
# View logs (Render)
render logs --tail

# View logs (Railway)
railway logs

# View logs (Fly.io)
fly logs

# View logs (Docker)
docker logs prewalk-generator

# Follow logs
docker logs -f prewalk-generator

# Check disk usage
df -h

# Check memory usage
free -m

# Check process
ps aux | grep python
```

### Appendix E: External Resources

#### Documentation
- **FastAPI**: https://fastapi.tiangolo.com/
- **OpenAI API**: https://platform.openai.com/docs
- **RapidAPI**: https://rapidapi.com/hub
- **python-docx**: https://python-docx.readthedocs.io/
- **Render**: https://render.com/docs
- **Power Automate**: https://learn.microsoft.com/en-us/power-automate/

#### Tools
- **Postman**: https://www.postman.com/
- **ngrok**: https://ngrok.com/
- **Docker**: https://www.docker.com/
- **Git**: https://git-scm.com/

#### Communities
- **FastAPI Discord**: https://discord.gg/fastapi
- **Python Discord**: https://discord.gg/python
- **Stack Overflow**: https://stackoverflow.com/questions/tagged/fastapi

#### Tutorials
- **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/
- **OpenAI Cookbook**: https://github.com/openai/openai-cookbook
- **Docker Tutorial**: https://docs.docker.com/get-started/

---

## Conclusion

This documentation provides a comprehensive overview of the Pre-Walkthrough Report Generator system, covering architecture, deployment, integration, and best practices. For questions or support, please refer to the troubleshooting section or contact the development team.

**System Version**: 1.0.0  
**Documentation Version**: 1.0.0  
**Last Updated**: November 25, 2025

---

**End of Documentation**
