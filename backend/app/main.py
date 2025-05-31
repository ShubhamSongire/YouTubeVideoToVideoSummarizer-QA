from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
import os
from typing import Dict, List, Optional
import uuid
import time
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
        
        # Transcribe audio
        if transcriber:
            video_store[processing_id]["steps"]["transcription"] = "in_progress"
            transcript = transcriber.transcribe(video_info["audio_path"])
            video_store[processing_id]["transcript"] = transcript["full_text"]
            video_store[processing_id]["segments"] = transcript["segments"]
            video_store[processing_id]["steps"]["transcription"] = "completed"
            logger.info(f"Transcription completed for video {video_id}")
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

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Ask a question about a specific video."""
    video_id = request.video_id
    
    # Find processing_id by video_id
    processing_id = None
    for pid, data in video_store.items():
        if data.get("video_id") == video_id and data["status"] == "completed":
            processing_id = pid
            break
    
    if processing_id is None:
        raise HTTPException(status_code=404, detail="Video not found or not processed")
    
    try:
        # Initialize RAG chain for this video
        vector_store = VectorStore()
        vector_store.load_vector_store(f"video_{video_id}")
        
        base_retriever = vector_store.get_retriever(k=4)
        enhanced_retriever = EnhancedRetriever(base_retriever, relevance_threshold=0.3)
        retriever = enhanced_retriever.setup_contextual_compression(vector_store.embeddings)
        
        rag_chain = RAGChain(
            retriever,
            model_manager,
            session_manager
        )
        
        # Create session if needed - FIXED: explicit error handling
        session_id = request.session_id
        try:
            if session_id is None:
                session_id = session_manager.create_session(metadata={"video_id": video_id})
            else:
                # Verify session exists or create it
                try:
                    session_manager.get_session(session_id)
                except ValueError:
                    # Session doesn't exist, create it
                    session_id = session_manager.create_session(
                        session_id=session_id, 
                        metadata={"video_id": video_id}
                    )
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