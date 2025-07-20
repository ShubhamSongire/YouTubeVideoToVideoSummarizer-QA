# Deployment Guide for YouTube Video QA Application

This guide covers how to deploy both the backend (FastAPI) and frontend (Streamlit) components of the YouTube Video QA application to popular cloud platforms.

## Prerequisites

- Git repository with your code
- API keys for OpenAI and/or Google Gemini
- Account on the deployment platform of your choice

## Deployment Options

### Option 1: Heroku Deployment

#### Backend Deployment (FastAPI)

1. **Create a new Heroku app for the backend**:
   ```bash
   heroku create yt-video-qa-backend
   ```

2. **Set up environment variables**:
   ```bash
   heroku config:set GOOGLE_API_KEY=your-google-key
   heroku config:set OPENAI_API_KEY=your-openai-key
   ```

3. **Deploy the backend**:
   ```bash
   git push heroku gemini-deploy:main
   ```

4. **Scale the dynos** (optional if you need more resources):
   ```bash
   heroku ps:scale web=1
   ```

#### Frontend Deployment (Streamlit)

1. **Create a new Heroku app for the frontend**:
   ```bash
   heroku create yt-video-qa-frontend
   ```

2. **Set up environment variables**:
   ```bash
   # Replace with your actual backend URL from the previous step
   heroku config:set API_URL=https://yt-video-qa-backend.herokuapp.com
   ```

3. **Deploy the frontend**:
   ```bash
   # From the project root
   git subtree push --prefix frontend/streamlit heroku main
   ```

### Option 2: Render Deployment

#### Backend Deployment (FastAPI)

1. **Create a new Web Service on Render**
   - Connect your GitHub repository
   - Select the branch: `gemini-deploy`
   - Set the build command: `pip install -r requirements.txt`
   - Set the start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add the environment variables (GOOGLE_API_KEY, etc.)

#### Frontend Deployment (Streamlit)

1. **Create a new Web Service on Render**
   - Connect your GitHub repository
   - Select the branch: `gemini-deploy`
   - Set the build command: `cd frontend/streamlit && pip install -r requirements.txt`
   - Set the start command: `cd frontend/streamlit && streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   - Add the environment variable `API_URL` pointing to your backend URL

### Option 3: Railway Deployment

#### Backend Deployment

1. Create a new project on Railway
2. Connect your GitHub repository
3. Configure the environment variables
4. Deploy the service
5. Note your generated URL for the backend

#### Frontend Deployment

1. Create a new project on Railway
2. Connect your GitHub repository
3. Set the root directory to `/frontend/streamlit`
4. Set the `API_URL` environment variable to your backend URL
5. Deploy the service

## Configuring Domains & HTTPS

For production use, configure custom domains and ensure HTTPS is enabled:

### Heroku
```bash
heroku domains:add api.yourdomain.com --app yt-video-qa-backend
heroku domains:add app.yourdomain.com --app yt-video-qa-frontend
```

### Render & Railway
Follow the respective platform's documentation to add custom domains.

## Monitoring & Scaling

### Heroku
- Monitor logs: `heroku logs --tail --app yt-video-qa-backend`
- Scale dynos: `heroku ps:scale web=2 --app yt-video-qa-backend`

### Render & Railway
Use the dashboard to monitor logs and adjust instance types as needed.

## Cost Considerations

- **Heroku**: Free tier has limits and will sleep after 30 minutes of inactivity
- **Render**: Free tier has similar limitations
- **Railway**: Usage-based pricing with a free tier limit

For production use, consider paid tiers that offer more resources and uptime.
