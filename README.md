# Pre-Walkthrough Report Generator

A FastAPI-based service that automatically generates comprehensive pre-walkthrough reports from property visit transcripts. The system extracts key information from transcripts, fetches property details from real estate APIs, and generates professional Word documents for real estate professionals.

## 🚀 Features

- **Transcript Processing**: Extracts key information from property visit transcripts
- **Property Data Integration**: Fetches property details, photos, and floor plans from real estate APIs
- **Automated Report Generation**: Creates professional Word documents with property information
- **Multiple Input Formats**: Supports text input and file uploads
- **RESTful API**: Easy integration with existing workflows
- **Real-time Processing**: Fast transcript analysis and report generation

## 🛠 Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **AI/ML**: OpenAI GPT for transcript processing
- **APIs**: RapidAPI for property data, SerpAPI for web search
- **Document Generation**: python-docx for Word document creation
- **Deployment**: Render (production), Docker support

## 📋 Prerequisites

- Python 3.11+
- OpenAI API key
- RapidAPI key (for property data)
- SerpAPI key (optional, for enhanced search)

## 🔧 Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pre-walkthrough-report-generator.git
   cd pre-walkthrough-report-generator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the server**
   ```bash
   python fastapi_server.py
   ```

The API will be available at `http://localhost:8000`

### Quick Start with Docker

```bash
docker build -t prewalk-generator .
docker run -p 8000:8000 --env-file .env prewalk-generator
```

## 🌐 Deployment

### Render (Recommended)

1. Fork this repository
2. Connect to Render
3. Set environment variables
4. Deploy automatically

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for detailed instructions.

### Other Platforms

- **Railway**: Use `railway.json` configuration
- **Fly.io**: Use `fly.toml` configuration
- **Heroku**: Standard Python buildpack

## 📖 API Documentation

### Endpoints

#### Health Check
```http
GET /health
```

#### Generate Report from File
```http
POST /generate-report
Content-Type: multipart/form-data

transcript_file: file
address: string (optional)
last_name: string (optional)
```

#### Generate Report from Text
```http
POST /generate-report-from-text
Content-Type: application/json

{
  "transcript_text": "string",
  "address": "string (optional)",
  "last_name": "string (optional)"
}
```

#### Configuration
```http
GET /config
```

### Response Format

All endpoints return JSON responses with appropriate HTTP status codes.

Example success response:
```json
{
  "message": "Report generated successfully",
  "filename": "PreWalkReport_Smith.docx"
}
```

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for transcript processing |
| `RAPIDAPI_KEY` | Yes | RapidAPI key for property data |
| `SERPAPI_KEY` | No | SerpAPI key for enhanced web search |
| `PORT` | No | Server port (default: 8000) |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

## 📁 Project Structure

```
├── fastapi_server.py          # Main FastAPI application
├── render_server.py           # Production server wrapper
├── config_manager.py          # Configuration management
├── pre_walkthrough_generator/ # Core processing modules
│   ├── src/
│   │   ├── transcript_processor.py
│   │   ├── property_api.py
│   │   └── document_generator.py
│   └── Pre-walkthrough_template.docx
├── data/                      # Generated reports
├── templates/                 # Document templates
├── requirements.txt           # Python dependencies
├── render.yaml               # Render deployment config
└── README.md                 # This file
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

Test deployment:
```bash
python test_deployment.py https://your-app-url.com
```

## 📊 Usage Examples

### Using cURL

```bash
# Health check
curl https://your-app.onrender.com/health

# Generate report from text
curl -X POST https://your-app.onrender.com/generate-report-from-text \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_text": "We visited 123 Main St today...",
    "address": "123 Main St, New York, NY 10001",
    "last_name": "Smith"
  }' \
  --output report.docx
```

### Using Python

```python
import requests

# Generate report
response = requests.post(
    "https://your-app.onrender.com/generate-report-from-text",
    json={
        "transcript_text": "Property visit transcript...",
        "address": "123 Main St, New York, NY 10001",
        "last_name": "Johnson"
    }
)

if response.status_code == 200:
    with open("report.docx", "wb") as f:
        f.write(response.content)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the [deployment guide](RENDER_DEPLOYMENT.md)
- **Issues**: Open an issue on GitHub
- **API Docs**: Visit `/docs` endpoint when server is running

## 🔄 Changelog

### v1.0.0
- Initial release
- FastAPI implementation
- Property data integration
- Automated report generation
- Render deployment support

## 🙏 Acknowledgments

- OpenAI for transcript processing capabilities
- RapidAPI for property data access
- FastAPI community for the excellent framework