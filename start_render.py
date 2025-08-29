#!/usr/bin/env python3
"""
Alternative startup script for Render deployment
This bypasses Gunicorn and uses Uvicorn directly
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

def main():
    try:
        # Import the FastAPI app
        from fastapi_server import app
        logger.info("Successfully imported FastAPI app")
        
        # Add a health check endpoint
        @app.get("/render-health")
        async def render_health():
            return {"status": "healthy", "service": "pre-walkthrough-generator"}
        
        # Start the server
        import uvicorn
        port = int(os.environ.get("PORT", 10000))
        host = "0.0.0.0"
        
        logger.info(f"Starting Uvicorn server on {host}:{port}")
        uvicorn.run(
            app, 
            host=host, 
            port=port,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        logger.error(f"Failed to import FastAPI app: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()