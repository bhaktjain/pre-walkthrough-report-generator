# Deployment Troubleshooting Guide

## The Problem
The error `FastAPI.__call__() missing 1 required positional argument: 'send'` occurs when trying to run a FastAPI application with a WSGI server like Gunicorn's default sync worker.

## The Solution
FastAPI is an ASGI application and requires an ASGI server. We have several options:

### Option 1: Gunicorn with Uvicorn Workers (Recommended)
```bash
gunicorn app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 1 --timeout 30
```

### Option 2: Pure Uvicorn
```bash
python -m uvicorn app:app --host 0.0.0.0 --port $PORT
```

### Option 3: Custom Startup Script
```bash
python start_render.py
```

## Files Created/Modified

1. **app.py** - Main entry point that Gunicorn expects
2. **render.yaml** - Updated with proper startCommand
3. **gunicorn.conf.py** - Gunicorn configuration (optional)
4. **start_render.py** - Alternative startup script using pure Uvicorn

## Testing Locally

To test if the configuration works:

```bash
# Install dependencies
pip install -r render_requirements.txt

# Test with Gunicorn + Uvicorn workers
gunicorn app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Test with pure Uvicorn
python -m uvicorn app:app --host 0.0.0.0 --port 8000

# Test with custom script
python start_render.py
```

## Render Deployment

The current render.yaml should work with:
```yaml
startCommand: gunicorn app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 1 --timeout 30
```

## Fallback Options

If the above doesn't work, try these alternatives in render.yaml:

### Alternative 1: Pure Uvicorn
```yaml
startCommand: python -m uvicorn app:app --host 0.0.0.0 --port $PORT
```

### Alternative 2: Custom Script
```yaml
startCommand: python start_render.py
```

### Alternative 3: Original Render Server
```yaml
startCommand: python -m uvicorn render_server:app --host 0.0.0.0 --port $PORT
```

## Health Check

Once deployed, test these endpoints:
- `GET /` - Main API info
- `GET /health` - Health check
- `GET /render-health` - Render-specific health check

## Common Issues

1. **Import Errors**: Make sure all dependencies are in render_requirements.txt
2. **Path Issues**: The app.py adds the pre_walkthrough_generator to Python path
3. **Port Issues**: Use `$PORT` environment variable, not hardcoded ports
4. **Worker Issues**: Start with 1 worker for free tier, increase for paid plans