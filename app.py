"""
Pre-Walkthrough Report Generator - Azure App Service Production Version
"""
import os
import logging
import tempfile
import shutil
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pre-Walkthrough Report Generator",
    description="API for generating pre-walkthrough reports from transcripts",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranscriptRequest(BaseModel):
    transcript_text: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Pre-Walkthrough Report Generator API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "generate_report": "/generate-report",
            "generate_from_text": "/generate-report-from-text"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pre-walkthrough-report-generator",
        "timestamp": "2025-07-07T17:50:00Z"
    }

@app.get("/test")
async def test():
    """Test endpoint"""
    return {
        "message": "API is working!",
        "timestamp": "2025-07-07T17:50:00Z"
    }

@app.post("/generate-report")
async def generate_report(transcript_file: UploadFile = File(...)):
    """Generate report from uploaded transcript file"""
    try:
        # Validate file type
        if not transcript_file.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="Only .txt files are supported")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
            shutil.copyfileobj(transcript_file.file, temp_file)
            temp_file_path = temp_file.name
        
        # For now, return a simple response indicating the file was received
        # In production, this would call your actual report generation logic
        return {
            "message": "File received successfully",
            "filename": transcript_file.filename,
            "size": transcript_file.size,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/generate-report-from-text")
async def generate_report_from_text(request: TranscriptRequest):
    """Generate report from transcript text"""
    try:
        # For now, return a simple response
        # In production, this would call your actual report generation logic
        return {
            "message": "Text received successfully",
            "text_length": len(request.transcript_text),
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

@app.get("/config")
async def get_config():
    """Get current configuration"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        # Don't expose API keys in response
        if 'api_keys' in config:
            config['api_keys'] = {k: '***' if v else '' for k, v in config['api_keys'].items()}
        return config
    except Exception as e:
        return {"error": f"Could not load config: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 