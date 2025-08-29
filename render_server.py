"""
Production FastAPI server for Render deployment
"""
import os
import logging
import sys
from pathlib import Path

# Set up logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the pre_walkthrough_generator to the path
sys.path.append(str(Path(__file__).parent / "pre_walkthrough_generator" / "src"))

# Import the main FastAPI app directly
from fastapi_server import app

# Health check for Render
@app.get("/render-health")
async def render_health():
    return {"status": "healthy", "service": "pre-walkthrough-generator"}

# Export the app for ASGI servers
application = app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)