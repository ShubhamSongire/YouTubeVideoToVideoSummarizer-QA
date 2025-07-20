from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
import os
import glob
import shutil
from typing import Dict, List, Optional, Union
import uuid
import time
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import your existing components
from .rag_system.document_processor import DocumentProcessor
from .rag_system.vector_store import VectorStore
from .rag_system.memory import SessionManager
from .rag_system.model import ModelManager
from .rag_system.retriever import EnhancedRetriever
from .rag_system.rag_chain import RAGChain
from .core.video_processor import VideoProcessor
from .core.transcriber import Transcriber
from .core.summarizer import TextSummarizer
from .rag_system.logger import setup_logger
from .cleanup import cleanup_video_files, cleanup_all_files, recreate_directories

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)

# Cloud environment detection
IS_CLOUD_ENV = any(os.environ.get(env) for env in [
    'RENDER', 'HEROKU', 'VERCEL', 'RAILWAY', 'FLY',
    'GOOGLE_CLOUD_PROJECT', 'AWS_LAMBDA_FUNCTION_NAME'
])

if IS_CLOUD_ENV:
    logger.info("Cloud environment detected - using cloud optimizations")

app = FastAPI(
    title="YouTube Video QA API",
    description="Cloud-optimized YouTube video analysis and Q&A system",
    version="2.0.0"
)

# Add CORS middleware to allow requests from the Streamlit app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create required directories
def create_required_directories():
    dirs = [
        "./downloads", 
        "./downloads/transcripts",
        "./downloads/vector_stores", 
        "./downloads/logs"
    ]
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"Created directory: {dir_path}")

# Create directories at startup
create_required_directories()

# Initialize components
video_processor = VideoProcessor(output_dir="./downloads")
try:
    transcriber = Transcriber(model_name="base")
    logger.info("Transcriber initialized successfully")
except Exception as e:
    logger.error(f"Error initializing transcriber: {str(e)}")
    logger.warning("Proceeding without transcriber")
    transcriber = None

summarizer = TextSummarizer()
session_manager = SessionManager()
model_manager = ModelManager(model_name="gemini-1.5-flash", temperature=0.0)

# In-memory store for processed videos
video_store = {}

class VideoRequest(BaseModel):
    youtube_url: HttpUrl
    
class QuestionRequest(BaseModel):
    video_id: str
    question: str
    session_id: Optional[str] = None

@app.get("/")
def read_root():
    return {"status": "running", "service": "YouTube Video QA API"}

@app.post("/process-video")
async def process_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Process a YouTube video (download, transcribe, vectorize)."""
    try:
        # Generate a processing ID
        processing_id = str(uuid.uuid4())
        
        # Store initial status
        video_store[processing_id] = {
            "status": "processing",
            "youtube_url": str(request.youtube_url),
            "created_at": time.time(),
            "steps": {
                "download": "pending",
                "transcription": "pending",
                "summarization": "pending",
                "vectorization": "pending"
            }
        }
        
        # Add task to background
        background_tasks.add_task(
            process_video_task, 
            processing_id, 
            str(request.youtube_url)
        )
        
        return {
            "processing_id": processing_id,
            "status": "processing",
            "message": "Video processing started"
        }
    
    except Exception as e:
        logger.error(f"Error processing video request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 

async def process_video_task(processing_id: str, youtube_url: str):
    """Background task for processing videos."""
    logger.info(f"Starting video processing for {youtube_url}")
    try:
        # Update status
        video_store[processing_id]["steps"]["download"] = "in_progress"
        
        # Download audio
        video_info = video_processor.download_audio(youtube_url)
        video_id = video_info["video_id"]
        video_store[processing_id]["video_id"] = video_id
        video_store[processing_id]["title"] = video_info["title"]
        video_store[processing_id]["steps"]["download"] = "completed"
        logger.info(f"Download completed for video {video_id}")
        
        # Transcribe audio
        video_store[processing_id]["steps"]["transcription"] = "in_progress"
        transcript = transcriber.transcribe(video_info["audio_path"])
        video_store[processing_id]["transcript"] = transcript["full_text"]
        video_store[processing_id]["segments"] = transcript["segments"]
        video_store[processing_id]["steps"]["transcription"] = "completed"
        
        # Generate summary
        video_store[processing_id]["steps"]["summarization"] = "in_progress"
        summary = summarizer.summarize(video_store[processing_id]["transcript"])
        video_store[processing_id]["summary"] = summary
        video_store[processing_id]["steps"]["summarization"] = "completed"
        logger.info(f"Summarization completed for video {video_id}")
        
        # Create vector store for this video
        video_store[processing_id]["steps"]["vectorization"] = "in_progress"
        
        # Create a document from transcript - store in downloads folder
        os.makedirs("./downloads/transcripts", exist_ok=True)
        text_path = f"./downloads/transcripts/{video_id}.txt"
        with open(text_path, "w") as f:
            f.write(video_store[processing_id]["transcript"])
            
        # Process the document for RAG
        doc_processor = DocumentProcessor()
        docs = doc_processor.load_documents("./downloads/transcripts")
        chunks = doc_processor.split_documents(docs)
        
        # Create vector store
        vector_store = VectorStore()
        vector_store.create_vector_store(chunks, f"video_{video_id}")
        
        video_store[processing_id]["steps"]["vectorization"] = "completed"
        video_store[processing_id]["status"] = "completed"
        logger.info(f"Video processing completed for {video_id}")
        
    except Exception as e:
        video_store[processing_id]["status"] = "failed"
        video_store[processing_id]["error"] = str(e)
        logger.error(f"Error processing video: {str(e)}")

@app.get("/video/{processing_id}")
async def get_video_status(processing_id: str):
    """Get status of video processing."""
    if processing_id not in video_store:
        raise HTTPException(status_code=404, detail="Processing ID not found")
    
    return video_store[processing_id]

@app.get("/video/{processing_id}/summary")
async def get_video_summary(processing_id: str):
    """Get the summary of a processed video."""
    if processing_id not in video_store:
        raise HTTPException(status_code=404, detail="Processing ID not found")
    
    video_data = video_store[processing_id]
    
    if video_data["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Video processing not completed. Current status: {video_data['status']}"
        )
    
    return {
        "processing_id": processing_id,
        "video_id": video_data["video_id"],
        "title": video_data["title"],
        "summary": video_data["summary"]
    }
    
@app.get("/video/{processing_id}/status")
async def check_processing_status(processing_id: str):
    """Check the status of a video processing task."""
    if processing_id not in video_store:
        raise HTTPException(status_code=404, detail="Processing task not found")
    
    data = video_store[processing_id]
    
    # Add vector store status to the response
    vector_store_exists = False
    if "video_id" in data:
        video_id = data['video_id']
        vector_store_name = f"video_{video_id}"
        vector_store_path = os.path.join("./downloads/vector_stores", vector_store_name)
        index_path = f"{vector_store_path}/index.faiss"
        docstore_path = f"{vector_store_path}/index.pkl"
        vector_store_exists = os.path.exists(index_path) and os.path.exists(docstore_path)
    
    return {
        "status": data["status"],
        "video_id": data.get("video_id"),
        "title": data.get("title"),
        "transcript_available": data.get("transcript_status") == "completed",
        "summary_available": data.get("summary_status") == "completed",
        "vector_store_available": vector_store_exists,  # Add this status
        "error": data.get("error")
    }
    
@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Ask a question about a specific video."""
    video_id = request.video_id
    
    # Debug: Print expected vector store path in downloads folder
    vector_store_name = f"video_{video_id}"
    vector_store_path = os.path.join("./downloads/vector_stores", vector_store_name)
    index_path = f"{vector_store_path}/index.faiss"
    docstore_path = f"{vector_store_path}/index.pkl"
    logger.info(f"Looking for vector store at: {vector_store_path}")
    logger.info(f"Index exists? {os.path.exists(index_path)}, Docstore exists? {os.path.exists(docstore_path)}")
    
    # Check if transcript exists
    transcript_path = f"./downloads/transcripts/{video_id}.txt"
    transcript_exists = os.path.exists(transcript_path)
    logger.info(f"Transcript path: {transcript_path}, exists: {transcript_exists}")
    
    # Check if vector store exists first in downloads folder
    if not (os.path.exists(index_path) and os.path.exists(docstore_path)):
        return JSONResponse(
            status_code=400,
            content={
                "error": "Video processing incomplete",
                "message": f"The vector store for video {video_id} is not ready yet. Please check processing status first."
            }
        )
    try:
        # Initialize RAG chain for this video
        vector_store = VectorStore()
        vector_store.load_vector_store(f"video_{video_id}")
        
        base_retriever = vector_store.get_retriever(k=4)
        enhanced_retriever = EnhancedRetriever(base_retriever, relevance_threshold=0.7)
        retriever = enhanced_retriever.setup_contextual_compression(vector_store.embeddings)
        
        rag_chain = RAGChain(
            retriever,
            model_manager,
            session_manager
        )
        
        # Create session if needed with video_id in metadata
        session_id = request.session_id
        try:
            if session_id is None:
                # Create new session with video_id in metadata
                session_id = session_manager.create_session(metadata={"video_id": video_id})
                logger.info(f"Created new session {session_id} for video {video_id}")
            else:
                # Verify session exists or create it
                try:
                    # Get existing session and update metadata if needed
                    session = session_manager.get_session(session_id)
                    if "metadata" not in session or "video_id" not in session["metadata"]:
                        session["metadata"] = {"video_id": video_id}
                        logger.info(f"Updated metadata for existing session {session_id}")
                except ValueError:
                    # Session doesn't exist, create it with video_id metadata
                    session_id = session_manager.create_session(
                        session_id=session_id, 
                        metadata={"video_id": video_id}
                    )
                    logger.info(f"Created session with ID {session_id} for video {video_id}")
        except Exception as session_error:
            logger.error(f"Session error: {str(session_error)}")
            session_id = None  # Fallback to None if session handling fails
        
        # Get answer
        logger.info(f"Processing question for video {video_id}: {request.question}")
        response = rag_chain.invoke(request.question, session_id)
        
        return {
            "video_id": video_id,
            "question": request.question,
            "answer": response.get("answer", "No answer generated"),
            "session_id": response.get("session_id", session_id)  # Use fallback if missing
        }
        
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/{processing_id}/transcript")
async def get_video_transcript(processing_id: str):
    """Get the transcript of a processed video."""
    if processing_id not in video_store:
        raise HTTPException(status_code=404, detail="Processing ID not found")
    
    video_data = video_store[processing_id]
    
    if video_data["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Video processing not completed. Current status: {video_data['status']}"
        )
    
    if "transcript" not in video_data:
        raise HTTPException(status_code=404, detail="Transcript not found for this video")
        
    # Return transcript and segments if available
    response = {
        "processing_id": processing_id,
        "video_id": video_data["video_id"],
        "title": video_data["title"],
        "transcript": video_data["transcript"]
    }
    
    # Add segments if available
    if "segments" in video_data:
        response["segments"] = video_data["segments"]
    
    # Add transcription source if available
    if "transcription_source" in video_data:
        response["transcription_source"] = video_data["transcription_source"]
    else:
        response["transcription_source"] = "unknown"
        
    return response

@app.post("/cleanup")
async def cleanup():
    """Cleanup utility to remove processed video files and data."""
    try:
        # Log cleanup start
        logger.info("Starting cleanup of processed videos and data")
        
        # Remove downloads folder
        if os.path.exists("./downloads"):
            shutil.rmtree("./downloads")
            logger.info("Removed downloads folder")
        
        # Clear in-memory video store
        video_store.clear()
        logger.info("Cleared in-memory video store")
        
        # Recreate necessary directories
        recreate_directories()
        
        return {"status": "success", "message": "Cleanup completed"}
    
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class CleanupRequest(BaseModel):
    video_id: Optional[str] = None
    clear_memory: bool = True  # Whether to clear from in-memory store too

@app.post("/cleanup/video")
async def cleanup_video(request: CleanupRequest):
    """Cleanup files for a specific video."""
    try:
        video_id = request.video_id
        
        if not video_id:
            raise HTTPException(status_code=400, detail="video_id is required")
        
        # Log cleanup start
        logger.info(f"Starting cleanup for video {video_id}")
        
        # Clean up files
        deleted_counts = cleanup_video_files(video_id)
        
        # Clear from in-memory store if requested
        if request.clear_memory:
            # Find all processing IDs that match this video_id
            processing_ids_to_remove = []
            for processing_id, data in video_store.items():
                if data.get("video_id") == video_id:
                    processing_ids_to_remove.append(processing_id)
            
            # Remove from video store
            for processing_id in processing_ids_to_remove:
                video_store.pop(processing_id, None)
                logger.info(f"Removed video {video_id} from in-memory store (processing_id: {processing_id})")
        
        return {
            "status": "success", 
            "message": f"Cleanup completed for video {video_id}",
            "deleted": deleted_counts
        }
    
    except Exception as e:
        logger.error(f"Error during video cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cleanup/all")
async def cleanup_all(request: CleanupRequest):
    """Cleanup all files but maintain directory structure."""
    try:
        # Log cleanup start
        logger.info("Starting cleanup of all files")
        
        # Clean up all files
        deleted_counts = cleanup_all_files()
        
        # Clear in-memory store if requested
        if request.clear_memory:
            video_store.clear()
            logger.info("Cleared in-memory video store")
        
        return {
            "status": "success", 
            "message": "All files cleaned up",
            "deleted": deleted_counts
        }
    
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/healthz")
def healthz():
    return {"status": "ok"}