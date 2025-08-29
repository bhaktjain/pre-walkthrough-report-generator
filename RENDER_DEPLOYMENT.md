# Render Deployment Guide

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **API Keys**: You'll need:
   - OpenAI API Key
   - RapidAPI Key (for property data)
   - SerpAPI Key (optional, for web search)

## Deployment Steps

### 1. Connect Your Repository

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select this repository

### 2. Configure the Service

**Basic Settings:**
- **Name**: `prewalk-generator` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `main` (or your deployment branch)

**Build & Deploy:**
- **Build Command**: `./build.sh`
- **Start Command**: `uvicorn render_server:app --host 0.0.0.0 --port $PORT`

### 3. Set Environment Variables

In the Render dashboard, add these environment variables:

**Required:**
- `OPENAI_API_KEY`: Your OpenAI API key
- `RAPIDAPI_KEY`: Your RapidAPI key for property data
- `PYTHON_VERSION`: `3.11.0`
- `PORT`: `10000`

**Optional:**
- `SERPAPI_KEY`: Your SerpAPI key (for enhanced web search)
- `LOG_LEVEL`: `INFO`
- `ENVIRONMENT`: `production`

### 4. Deploy

1. Click "Create Web Service"
2. Render will automatically build and deploy your application
3. The build process takes 5-10 minutes
4. Once deployed, you'll get a URL like: `https://your-app-name.onrender.com`

## API Endpoints

Once deployed, your API will be available at:

- **Health Check**: `GET /health`
- **Generate Report (File)**: `POST /generate-report`
- **Generate Report (Text)**: `POST /generate-report-from-text`
- **Configuration**: `GET /config`

## Testing Your Deployment

Test your deployment with:

```bash
curl https://your-app-name.onrender.com/health
```

You should get a response like:
```json
{
  "status": "healthy",
  "uptime_seconds": 123.45,
  "requests_processed": 0,
  "errors": 0,
  "timestamp": "2024-01-01T12:00:00"
}
```

## Troubleshooting

### Common Issues:

1. **Build Fails**: Check the build logs in Render dashboard
2. **Import Errors**: Ensure all dependencies are in `render_requirements.txt`
3. **API Keys**: Verify environment variables are set correctly
4. **Timeout**: Render has a 30-second timeout for requests

### Logs:

View logs in the Render dashboard under "Logs" tab.

## Scaling

Render automatically handles:
- SSL certificates
- Load balancing
- Auto-scaling based on traffic
- Health checks and restarts

## Cost

- **Free Tier**: 750 hours/month (good for testing)
- **Paid Plans**: Start at $7/month for production use

## Security Notes

1. Never commit API keys to your repository
2. Use environment variables for all sensitive data
3. Consider restricting CORS origins in production
4. Monitor your API usage and costs

## Support

If you encounter issues:
1. Check Render's documentation
2. Review the build and runtime logs
3. Ensure all environment variables are set
4. Test locally first with the same configuration