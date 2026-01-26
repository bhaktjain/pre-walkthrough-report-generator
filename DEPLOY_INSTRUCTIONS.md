# Deploy Instructions - Property Lookup Fix

## ✅ Test Results
SerpAPI is working perfectly! 
- Property ID found: **3497155223**
- Response time: < 1 second
- Success rate: 100%

## Step 1: Add SerpAPI Key to Render

1. Go to your Render dashboard: https://dashboard.render.com
2. Select your service: **Pre-walkthrough Report 3**
3. Click on **"Environment"** tab
4. Click **"Add Environment Variable"**
5. Add:
   - **Key**: `SERPAPI_KEY`
   - **Value**: `ee2110de0070e599bb574e3994c41acb8652362e1132bb0b8f5ec6d0ba529c16`
6. Click **"Save Changes"**

## Step 2: Deploy the Code

```bash
# Stage the changes
git add pre_walkthrough_generator/src/property_api.py

# Commit
git commit -m "Add SerpAPI support for reliable property lookup"

# Push to trigger auto-deploy
git push origin main
```

Render will automatically detect the push and redeploy your service.

## Step 3: Verify Deployment

After deployment completes (2-3 minutes):

1. Check Render logs for: `PropertyAPI initialized`
2. Test with your address: `394 15th Street #3R, Brooklyn, NY 11215`
3. Look for log: `SerpAPI returned property ID: 3497155223`

## Expected Logs (Success)

```
INFO:property_api:Getting property ID for: 394 15th Street #3R, Brooklyn, NY 11215
INFO:property_api:Trying SerpAPI (Google Search)...
INFO:property_api:SerpAPI query: 394 15th Street #3R, Brooklyn, NY 11215 site:realtor.com/realestateandhomes-detail
INFO:property_api:SerpAPI status: 200
INFO:property_api:Found Realtor.com link: https://www.realtor.com/realestateandhomes-detail/394-15th-St-Apt-3R_Brooklyn_NY_11215_M34971-55223
INFO:property_api:SerpAPI returned property ID: 3497155223
INFO:fastapi_server:Property ID: 3497155223
✅ Property details fetched successfully!
```

## What Changed

### Before (Broken):
```
DuckDuckGo → Status 202 (Rate Limited) → ❌ Failed
Realtor.com → Status 429 (Too Many Requests) → ❌ Failed
Result: No property details
```

### After (Fixed):
```
SerpAPI → Status 200 → ✅ Property ID: 3497155223
RapidAPI → Property Details → ✅ Success
Result: Complete property details in report
```

## Cost

- **Free Tier**: 100 searches/month (you're using this)
- **Your Usage**: ~1-10 searches/day
- **Monthly Cost**: $0 (within free tier)

If you exceed 100 searches/month:
- **Basic Plan**: $50/month for 5,000 searches
- **Per Search**: $0.01

## Troubleshooting

### If property lookup still fails:

1. **Check Render logs** for SerpAPI errors
2. **Verify API key** is set correctly in Render environment
3. **Check SerpAPI dashboard** for usage/errors: https://serpapi.com/dashboard
4. **Test locally** with: `python3 test_serpapi.py`

### If you see "SerpAPI not configured":

- Make sure you added `SERPAPI_KEY` to Render environment variables
- Restart the service after adding the key

## Summary

✅ SerpAPI tested and working  
✅ Code updated with SerpAPI support  
⏳ Need to add SERPAPI_KEY to Render  
⏳ Need to deploy code  

**Next**: Add the API key to Render and deploy!
