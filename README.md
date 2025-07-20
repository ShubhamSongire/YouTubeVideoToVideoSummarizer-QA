# YouTubeVideoToVideoSummarizer-QA

Intelligent Video Knowledge Extraction: YouTubeVideoToVideoSummarizer is a powerful tool that transforms YouTube videos into queryable knowledge bases using advanced Retrieval Augmented Generation (RAG) technology.

## Features

- **Video Processing**: Download and process YouTube videos
- **Automatic Transcription**: Generate accurate transcripts of video content
- **Summarization**: Create concise summaries of video content
- **Q&A Interface**: Ask questions about the video content
- **Full Transcript Access**: View, search, and download the complete video transcript
- **Cleanup Utilities**: Manage disk space by cleaning up processed files
- **Multiple AI Models**: Support for both OpenAI and Google Gemini models

## Architecture

The system consists of two main components:

1. **Backend API (FastAPI)**: Handles video processing, transcription, summarization, and RAG
2. **Frontend (Streamlit)**: Provides a user-friendly interface for interacting with the system

## Setup & Installation

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/ShubhamSongire/YouTubeVideoToVideoSummarizer-QA.git
   cd YouTubeVideoToVideoSummarizer-QA
   ```

2. Set up Python environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with your API keys:
   ```
   OPENAI_API_KEY=your-openai-key
   GOOGLE_API_KEY=your-google-gemini-key
   ```

4. Start the backend server:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8080
   ```

5. In a separate terminal, start the Streamlit frontend:
   ```bash
   cd frontend/streamlit
   streamlit run app.py
   ```

6. Open your browser and navigate to `http://localhost:8501`

### Deployment

The application can be deployed using platforms like Heroku or Render:

#### Backend Deployment (FastAPI)

1. Set the following environment variables on your deployment platform:
   - `OPENAI_API_KEY`: Your OpenAI API key (optional)
   - `GOOGLE_API_KEY`: Your Google Gemini API key
   - `PORT`: The port for your application (set by the platform)

2. Deploy using the `Procfile` in the root directory.

#### Frontend Deployment (Streamlit)

1. Set the following environment variables:
   - `API_URL`: The URL of your deployed backend API
   - `PORT`: The port for your Streamlit app (set by the platform)

2. Deploy using the `Procfile` in the `frontend/streamlit` directory.

## Usage

1. Enter a YouTube URL in the sidebar
2. Click "Process Video" to download and analyze the video
3. View the summary in the Summary tab
4. Ask questions about the video content in the Q&A tab
5. View or download the full transcript in the Transcript tab
6. Manage disk space with the cleanup options in the Cleanup tab
