# Architecture Diagrams
## Pre-Walkthrough Report Generator

Visual representations of system architecture, data flows, and integrations.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │ Power        │  │ Web Browser  │  │ Mobile App   │  │ CLI Tool    ││
│  │ Automate     │  │ (Postman)    │  │              │  │             ││
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘│
│         │                  │                  │                  │       │
│         └──────────────────┴──────────────────┴──────────────────┘       │
│                                    │                                      │
└────────────────────────────────────┼──────────────────────────────────────┘
                                     │
                                     │ HTTPS
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY LAYER                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      FastAPI Server                                │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │  │
│  │  │ Request     │  │ Validation  │  │ Error       │              │  │
│  │  │ Handler     │  │ (Pydantic)  │  │ Handler     │              │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │  │
│  │                                                                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │  │
│  │  │ File Upload │  │ Metrics     │  │ Logging     │              │  │
│  │  │ Handler     │  │ Tracker     │  │ System      │              │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       PROCESSING LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │              Transcript Processor                                  │  │
│  │  ┌──────────────────────────────────────────────────────────┐    │  │
│  │  │  • Clean transcript                                       │    │  │
│  │  │  • Extract structured data (GPT-4o)                      │    │  │
│  │  │  • Parse address                                          │    │  │
│  │  │  • Analyze client profile                                │    │  │
│  │  └──────────────────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │              Property API Handler                                  │  │
│  │  ┌──────────────────────────────────────────────────────────┐    │  │
│  │  │  • Web scraping (DuckDuckGo, Realtor.com)              │    │  │
│  │  │  • Property ID resolution                                │    │  │
│  │  │  • RapidAPI integration                                  │    │  │
│  │  │  • Image & floor plan fetching                           │    │  │
│  │  └──────────────────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │              Document Generator                                    │  │
│  │  ┌──────────────────────────────────────────────────────────┐    │  │
│  │  │  • Word document assembly                                │    │  │
│  │  │  • Image embedding & conversion                          │    │  │
│  │  │  • Table formatting                                      │    │  │
│  │  │  • Hyperlink creation                                    │    │  │
│  │  └──────────────────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │ OpenAI API   │  │ RapidAPI     │  │ SerpAPI      │  │ Realtor.com ││
│  │ (GPT-4o)     │  │ (Property)   │  │ (Optional)   │  │ (Scraping)  ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘│
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────┐
│  Transcript │
│   Input     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  1. VALIDATION                      │
│  • Check length (50-100k chars)     │
│  • Verify format                    │
│  • Sanitize input                   │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  2. TRANSCRIPT PROCESSING           │
│  ┌───────────────────────────────┐  │
│  │ OpenAI GPT-4o                 │  │
│  │ • Extract property info       │  │
│  │ • Extract client info         │  │
│  │ • Extract renovation scope    │  │
│  │ • Extract timeline            │  │
│  │ • Extract materials           │  │
│  └───────────────────────────────┘  │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  3. ADDRESS RESOLUTION              │
│  • Use provided address OR          │
│  • Extract from transcript OR       │
│  • Parse from filename              │
│  • Clean & standardize              │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  4. PROPERTY ID LOOKUP              │
│  ┌───────────────────────────────┐  │
│  │ Try DuckDuckGo Search         │  │
│  │   ↓ (if fails)                │  │
│  │ Try Realtor.com Search        │  │
│  │   ↓ (if fails)                │  │
│  │ Try SerpAPI (if configured)   │  │
│  │   ↓ (if fails)                │  │
│  │ Construct from components     │  │
│  └───────────────────────────────┘  │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  5. PROPERTY DATA ENRICHMENT        │
│  ┌───────────────────────────────┐  │
│  │ RapidAPI: /v2/property        │  │
│  │ • Price, beds, baths, sqft    │  │
│  │ • Year built, type, HOA       │  │
│  │ • Neighborhood                │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ RapidAPI: /propertyPhotos     │  │
│  │ • Property images             │  │
│  │ • Floor plans                 │  │
│  └───────────────────────────────┘  │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  6. DATA ASSEMBLY                   │
│  • Combine transcript data          │
│  • Combine property data            │
│  • Validate completeness            │
│  • Format for document              │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  7. DOCUMENT GENERATION             │
│  • Create Word document             │
│  • Add header/footer images         │
│  • Generate sections:               │
│    - Executive Summary              │
│    - Property Details               │
│    - Client Details                 │
│    - Property Links                 │
│    - Floor Plans                    │
│    - Building Requirements          │
│    - Renovation Scope               │
│    - Timeline & Phasing             │
│    - Budget Summary                 │
│    - Notes                          │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────┐
│  Generated  │
│  .docx File │
└─────────────┘
```

---

## Power Automate Integration Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    TRIGGER OPTIONS                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Email        │  │ SharePoint   │  │ Scheduled    │      │
│  │ Arrives      │  │ File Upload  │  │ Recurrence   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    PREPROCESSING                             │
│  • Extract transcript text                                   │
│  • Parse metadata (address, name)                           │
│  • Validate content                                          │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    HTTP ACTION                               │
│  POST /generate-report-from-text                            │
│  {                                                           │
│    "transcript_text": "...",                                │
│    "address": "...",                                        │
│    "last_name": "..."                                       │
│  }                                                           │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    RESPONSE HANDLING                         │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │ Success (200)   │         │ Error (4xx/5xx) │           │
│  │ • Get .docx     │         │ • Log error     │           │
│  │ • Save file     │         │ • Notify admin  │           │
│  └────────┬────────┘         └────────┬────────┘           │
│           │                           │                     │
└───────────┼───────────────────────────┼─────────────────────┘
            │                           │
            ▼                           ▼
┌─────────────────────┐    ┌─────────────────────┐
│  SUCCESS ACTIONS    │    │  ERROR ACTIONS      │
│  • Send email       │    │  • Send error email │
│  • Save to SP       │    │  • Log to list      │
│  • Update CRM       │    │  • Retry logic      │
│  • Notify user      │    │  • Alert admin      │
└─────────────────────┘    └─────────────────────┘
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Local Machine                                         │ │
│  │  • Python 3.11+                                        │ │
│  │  • Virtual environment                                 │ │
│  │  • .env file with API keys                            │ │
│  │  • uvicorn --reload                                    │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ git push
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    VERSION CONTROL                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  GitHub Repository                                     │ │
│  │  • Source code                                         │ │
│  │  • Configuration files                                 │ │
│  │  • Documentation                                       │ │
│  │  • CI/CD workflows                                     │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ Auto-deploy
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Render / Railway / Fly.io / Azure                     │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  Load Balancer                                   │ │ │
│  │  └────────────────┬─────────────────────────────────┘ │ │
│  │                   │                                    │ │
│  │  ┌────────────────┴─────────────────────────────────┐ │ │
│  │  │  Application Instances                           │ │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │ │ │
│  │  │  │ Instance │  │ Instance │  │ Instance │      │ │ │
│  │  │  │    1     │  │    2     │  │    3     │      │ │ │
│  │  │  └──────────┘  └──────────┘  └──────────┘      │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  │                                                        │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  Monitoring & Logging                            │ │ │
│  │  │  • Health checks                                 │ │ │
│  │  │  • Error tracking (Sentry)                       │ │ │
│  │  │  • Performance monitoring (New Relic)            │ │ │
│  │  │  • Log aggregation                               │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Layer 1: Network Security                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  • HTTPS/TLS encryption                                │ │
│  │  • SSL certificates (Let's Encrypt)                    │ │
│  │  • Firewall rules                                      │ │
│  │  • DDoS protection                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  Layer 2: Application Security                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  • Input validation (Pydantic)                         │ │
│  │  • Rate limiting (SlowAPI)                             │ │
│  │  • CORS configuration                                  │ │
│  │  • Request size limits                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  Layer 3: Data Security                                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  • API key encryption                                  │ │
│  │  • Environment variable isolation                      │ │
│  │  • PII sanitization in logs                            │ │
│  │  • Secure file handling                                │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  Layer 4: Access Control                                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  • API authentication (future)                         │ │
│  │  • Role-based access control                           │ │
│  │  • Audit logging                                       │ │
│  │  • Session management                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
┌─────────────┐
│   Request   │
│   Received  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Try: Process Request               │
│  ┌───────────────────────────────┐  │
│  │ • Validate input              │  │
│  │ • Process transcript          │  │
│  │ • Fetch property data         │  │
│  │ • Generate document           │  │
│  └───────────────────────────────┘  │
└──────┬──────────────────────────────┘
       │
       ├─ Success ──────────────────────┐
       │                                 │
       ├─ ValidationError ───────────────┤
       │                                 │
       ├─ ExternalAPIError ──────────────┤
       │                                 │
       ├─ TimeoutError ──────────────────┤
       │                                 │
       └─ UnexpectedError ───────────────┤
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Error Handler                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  1. Log error details                                  │ │
│  │     • Timestamp                                        │ │
│  │     • Error type                                       │ │
│  │     • Stack trace                                      │ │
│  │     • Request context                                  │ │
│  │                                                         │ │
│  │  2. Determine error type                               │ │
│  │     • 400: Bad Request                                 │ │
│  │     • 422: Validation Error                            │ │
│  │     • 500: Internal Server Error                       │ │
│  │     • 503: Service Unavailable                         │ │
│  │     • 504: Gateway Timeout                             │ │
│  │                                                         │ │
│  │  3. Format error response                              │ │
│  │     {                                                  │ │
│  │       "detail": "User-friendly message",              │ │
│  │       "request_id": "uuid",                           │ │
│  │       "timestamp": "ISO 8601"                         │ │
│  │     }                                                  │ │
│  │                                                         │ │
│  │  4. Cleanup resources                                  │ │
│  │     • Delete temp files                                │ │
│  │     • Close connections                                │ │
│  │     • Release memory                                   │ │
│  │                                                         │ │
│  │  5. Update metrics                                     │ │
│  │     • Increment error counter                          │ │
│  │     • Track error type                                 │ │
│  │     • Alert if threshold exceeded                      │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────┐
│  Return Error Response              │
│  • HTTP status code                 │
│  • Error message                    │
│  • Request ID for tracking          │
└─────────────────────────────────────┘
```

---

**End of Architecture Diagrams**
