#!/usr/bin/env python3
"""
Production FastAPI server for Render deployment
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
    from fastapi_server import app
    logger.info("Successfully imported FastAPI app")
    
    # Add a health check endpoint
    @app.get("/render-health")
    async def render_health():
        return {"status": "healthy", "service": "pre-walkthrough-generator"}
    
except ImportError as e:
    logger.error(f"Failed to import FastAPI app: {e}")
    raise

# This is the ASGI application that uvicorn will use
# Make sure it's available at module level
application = app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)