"""
Production FastAPI server for Render deployment
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Set up logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the main FastAPI app
from fastapi_server import app

# Add production middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this more restrictively in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check for Render
@app.get("/render-health")
async def render_health():
    return {"status": "healthy", "service": "pre-walkthrough-generator"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)