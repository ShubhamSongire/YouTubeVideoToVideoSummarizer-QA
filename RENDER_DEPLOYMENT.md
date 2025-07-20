# Cloud Deployment Configuration for YouTube Video QA

## Environment Variables for Render.com

Add these environment variables in your Render service settings:

```bash
# Core API Configuration
GOOGLE_API_KEY_1=your_primary_key_here
GOOGLE_API_KEY_2=your_secondary_key_here
GOOGLE_API_KEY_3=your_tertiary_key_here
# ... add more keys for better rotation

# YouTube Download Configuration
YOUTUBE_DOWNLOAD_RETRIES=5
YOUTUBE_SLEEP_INTERVAL=3
YOUTUBE_MAX_SLEEP=8
YOUTUBE_USER_AGENT=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36

# Rate Limiting (helps avoid 429 errors)
ENABLE_RATE_LIMITING=true
RATE_LIMIT_DELAY_MIN=2
RATE_LIMIT_DELAY_MAX=5

# OpenMP Fix (prevents library conflicts)
KMP_DUPLICATE_LIB_OK=TRUE
OMP_NUM_THREADS=1

# Python Configuration
PYTHONPATH=/opt/render/project/src
PYTHONUNBUFFERED=1
```

## Build Command for Render

```bash
pip install -r requirements.txt && pip install --upgrade yt-dlp
```

## Start Command for Backend

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Start Command for Frontend (Streamlit)

```bash
cd frontend/streamlit && streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

## Common Cloud Issues & Solutions

### 1. Rate Limiting (429 Errors)
**Cause**: Cloud IPs are heavily rate-limited by YouTube
**Solutions**:
- Implemented multiple fallback strategies
- Added random delays between requests
- Using mobile client emulation
- Multiple user agents rotation

### 2. Geo-blocking
**Cause**: Content restricted in cloud server regions
**Solutions**:
- Android client emulation (often bypasses some restrictions)
- Fallback to lower quality streams
- Better error messaging for users

### 3. Memory Issues
**Cause**: Limited memory on free tiers
**Solutions**:
- Lower quality audio extraction (128kbps fallback)
- Cleanup temporary files immediately
- Process videos sequentially, not in parallel

### 4. Timeout Issues
**Cause**: Slow network on shared infrastructure
**Solutions**:
- Increased retry counts
- Progressive backoff strategy
- Connection keep-alive headers

## Testing Your Deployment

1. **Test with a simple video first**:
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

2. **Check logs for specific error patterns**:
   - Look for "429" errors (rate limiting)
   - Look for "geo-blocked" messages
   - Monitor memory usage

3. **Verify environment variables are set**:
   - All API keys are present
   - OpenMP settings applied
   - Rate limiting enabled

## Monitoring

Monitor these metrics in your Render dashboard:
- Response times (should be < 30s for most videos)
- Memory usage (should stay under limit)
- Error rates (aim for < 5%)
- API key rotation (ensure even distribution)

## Fallback Strategy

If YouTube downloads continue to fail:
1. Consider implementing a proxy service
2. Use alternative video sources
3. Implement local caching
4. Consider moving to a VPS with residential IP
