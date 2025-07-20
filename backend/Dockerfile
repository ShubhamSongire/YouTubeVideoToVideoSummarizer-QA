# Use official Python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Expose port (Render sets $PORT)
EXPOSE 8080

# Set environment variables (optional, can be set in Render dashboard)
# ENV OPENAI_API_KEY=your-openai-key
# ENV GOOGLE_API_KEY=your-google-gemini-key

# Start FastAPI app with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
