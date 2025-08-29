#!/usr/bin/env python3
"""
WSGI-compatible entry point for Gunicorn deployment
This file provides compatibility between FastAPI (ASGI) and Gunicorn (WSGI)
"""
import os
import sys
import logging
from pathlib import Path

# Add the pre_walkthrough_generator to the path
sys.path.append(str(Path(__file__).parent / "pre_walkthrough_generator" / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Import the main FastAPI app
    from fastapi_server import app as fastapi_app
    logger.info("Successfully imported FastAPI app")
    
    # Add a health check endpoint
    @fastapi_app.get("/render-health")
    async def render_health():
        return {"status": "healthy", "service": "pre-walkthrough-generator"}
    
    # For ASGI compatibility (uvicorn)
    app = fastapi_app
    
    # For WSGI compatibility (gunicorn with uvicorn workers)
    # This will be used when running with: gunicorn app:app -k uvicorn.workers.UvicornWorker
    application = fastapi_app
    
except ImportError as e:
    logger.error(f"Failed to import FastAPI app: {e}")
    logger.error("Check that all dependencies are installed correctly")
    raise

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)