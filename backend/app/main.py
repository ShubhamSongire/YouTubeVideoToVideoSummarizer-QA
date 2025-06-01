from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
import os
from typing import Dict, List, Optional
import uuid
import time
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Import your existing components
from app.rag_system.document_processor import DocumentProcessor
from app.rag_system.vector_store import VectorStore
from app.rag_system.memory import SessionManager
from app.rag_system.model import ModelManager
from app.rag_system.retriever import EnhancedRetriever
from app.rag_system.rag_chain import RAGChain
from app.core.video_processor import VideoProcessor
from app.core.transcriber import Transcriber
from app.core.summarizer import TextSummarizer
from app.rag_system.logger import setup_logger

# Load environment variables
load_dotenv()

# Create logger
logger = setup_logger(__name__)

# Create FastAPI instance
app = FastAPI(title="YouTube Video QA API")

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
model_manager = ModelManager(model_name="gpt-3.5-turbo")

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
        
        # Transcribe audio (using captions if available, or Whisper as fallback)
        if transcriber:
            video_store[processing_id]["steps"]["transcription"] = "in_progress"
            
            # Log whether we're using existing subtitles or Whisper
            if "subtitle_path" in video_info:
                logger.info(f"Using existing subtitles found at: {video_info['subtitle_path']}")
            else:
                logger.info(f"No subtitles found, will use Whisper for transcription")
                
            # Get transcript (will try captions first, then Whisper)
            transcript = transcriber.transcribe(video_info["audio_path"])
            
            video_store[processing_id]["transcript"] = transcript["full_text"]
            video_store[processing_id]["segments"] = transcript["segments"]
            video_store[processing_id]["steps"]["transcription"] = "completed"
            
            # Store the source of transcription
            video_store[processing_id]["transcription_source"] = "captions" if "subtitle_path" in video_info else "whisper"
            
            logger.info(f"Transcription completed for video {video_id} using {video_store[processing_id]['transcription_source']}")
        else:
            video_store[processing_id]["steps"]["transcription"] = "skipped"
            logger.warning("Transcriber not available, skipping transcription")
            # Use a placeholder transcript for testing if necessary
            video_store[processing_id]["transcript"] = "Placeholder transcript for testing."
        
        # Generate summary
        video_store[processing_id]["steps"]["summarization"] = "in_progress"
        summary = summarizer.summarize(video_store[processing_id]["transcript"])
        video_store[processing_id]["summary"] = summary
        video_store[processing_id]["steps"]["summarization"] = "completed"
        logger.info(f"Summarization completed for video {video_id}")
        
        # Create vector store for this video
        video_store[processing_id]["steps"]["vectorization"] = "in_progress"
        
        # Create a document from transcript
        os.makedirs("./transcripts", exist_ok=True)
        text_path = f"./transcripts/{video_id}.txt"
        with open(text_path, "w") as f:
            f.write(video_store[processing_id]["transcript"])
            
        # Process the document for RAG
        doc_processor = DocumentProcessor()
        docs = doc_processor.load_documents("./transcripts")
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
        vector_store_path = f"vector_stores/video_{data['video_id']}"
        vector_store_exists = os.path.exists(vector_store_path)
    
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
    
    # Debug: Print expected vector store path
    vector_store_path = f"video_{video_id}"
    actual_path = os.path.abspath(vector_store_path)
    logger.info(f"Looking for vector store at: {actual_path}")
    logger.info(f"Path exists? {os.path.exists(vector_store_path)}")
    
    # Check if transcript exists
    transcript_path = f"./transcripts/{video_id}.txt"
    transcript_exists = os.path.exists(transcript_path)
    logger.info(f"Transcript path: {transcript_path}, exists: {transcript_exists}")
    
    # Check if vector store exists first
    if not os.path.exists(vector_store_path):
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