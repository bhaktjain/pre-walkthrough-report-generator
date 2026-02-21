# Quick Reference Guide
## Pre-Walkthrough Report Generator

---

## API Endpoints

### Base URL
```
Production: https://your-app.onrender.com
Local: http://localhost:8000
```

### Health Check
```bash
GET /health
```

### Generate Report (File Upload)
```bash
POST /generate-report
Content-Type: multipart/form-data

Parameters:
- transcript_file (file, required)
- address (string, optional)
- last_name (string, optional)
```

### Generate Report (JSON)
```bash
POST /generate-report-from-text
Content-Type: application/json

Body:
{
  "transcript_text": "string",
  "address": "string (optional)",
  "last_name": "string (optional)"
}
```

---

## cURL Examples

### Health Check
```bash
curl https://your-app.onrender.com/health
```

### Generate from File
```bash
curl -X POST https://your-app.onrender.com/generate-report \
  -F "transcript_file=@transcript.txt" \
  -F "address=123 Main St, Brooklyn, NY" \
  -F "last_name=Smith" \
  --output report.docx
```

### Generate from Text
```bash
curl -X POST https://your-app.onrender.com/generate-report-from-text \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "Transcript content...",
    "address": "123 Main St, Brooklyn, NY",
    "last_name": "Smith"
  }' \
  --output report.docx
```

---

## Python Examples

### Basic Usage
```python
import requests

url = "https://your-app.onrender.com/generate-report-from-text"
data = {
    "transcript_text": "Transcript content...",
    "address": "123 Main St, Brooklyn, NY",
    "last_name": "Smith"
}

response = requests.post(url, json=data)

if response.status_code == 200:
    with open("report.docx", "wb") as f:
        f.write(response.content)
    print("Success!")
```

### With Error Handling
```python
import requests

try:
    response = requests.post(url, json=data, timeout=300)
    response.raise_for_status()
    
    with open("report.docx", "wb") as f:
        f.write(response.content)
    print("Report generated successfully!")
    
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

---

## Environment Variables

### Required
```env
OPENAI_API_KEY=sk-your-key
RAPIDAPI_KEY=your-key
```

### Optional
```env
SERPAPI_KEY=your-key
PORT=8000
LOG_LEVEL=INFO
```

---

## Common Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn fastapi_server:app --reload

# Run with gunicorn
gunicorn app:app -k uvicorn.workers.UvicornWorker
```

### Docker
```bash
# Build
docker build -t prewalk-generator .

# Run
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-key \
  -e RAPIDAPI_KEY=key \
  prewalk-generator

# Logs
docker logs prewalk-generator
```

### Deployment
```bash
# Render (auto-deploy on push)
git push origin main

# Railway
railway up

# Fly.io
fly deploy
```

---

## Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Report generated |
| 400 | Bad Request | Check input data |
| 404 | Not Found | Check endpoint URL |
| 422 | Validation Error | Fix request format |
| 500 | Server Error | Check logs |
| 503 | Service Unavailable | External API issue |
| 504 | Timeout | Increase timeout |

---

## Troubleshooting

### "Empty transcript" error
- Ensure transcript has at least 50 characters
- Check for meaningful content

### "Property ID not found"
- Verify address format
- Check if property exists on Realtor.com
- Try manual search first

### "Timeout" error
- Increase timeout to 5 minutes
- Check server logs
- Verify API keys are valid

### "Image download failed"
- Check internet connection
- Verify image URLs are accessible
- Try again later

---

## File Locations

```
project/
├── fastapi_server.py          # Main API server
├── app.py                     # ASGI entry point
├── config_manager.py          # Configuration
├── requirements.txt           # Dependencies
├── .env                       # Environment variables
├── header.png                 # Header image
├── footer.png                 # Footer image
├── data/                      # Generated reports
├── templates/                 # Document templates
└── pre_walkthrough_generator/
    └── src/
        ├── transcript_processor.py
        ├── property_api.py
        └── document_generator.py
```

---

## API Keys

### OpenAI
- Get key: https://platform.openai.com/api-keys
- Pricing: $5/1M input tokens, $15/1M output tokens
- Model: gpt-4o

### RapidAPI
- Get key: https://rapidapi.com/hub
- Subscribe to: US Real Estate Listings
- Free tier available

### SerpAPI (Optional)
- Get key: https://serpapi.com/
- Pricing: $50/month for 5,000 searches
- Alternative: Free DuckDuckGo scraping

---

## Support

- Documentation: See COMPLETE_SYSTEM_DOCUMENTATION.md
- Power Automate: See POWER_AUTOMATE_INTEGRATION_GUIDE.md
- Issues: Check troubleshooting section
- API Docs: https://your-app.onrender.com/docs

---

**Version**: 1.0.0  
**Last Updated**: November 25, 2025
