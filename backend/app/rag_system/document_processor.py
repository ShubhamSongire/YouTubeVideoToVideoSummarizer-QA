from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List, Dict, Any
from .logger import setup_logger
import logging

logger = setup_logger(__name__)

class DocumentProcessor:
    """Handles document loading and processing with optimized chunking for Gemini models."""
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        """Initialize document processor with optimized chunk parameters for Gemini."""
        logger.info(f"Initializing DocumentProcessor with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True
        )
    
    def load_documents(self, directory_path: str):
        """Load all text documents from a directory."""
        logger.info(f"Loading documents from directory: {directory_path}")
        try:
            loader = DirectoryLoader(
                directory_path,
                glob="**/*.txt",
                loader_cls=TextLoader
            )
            documents = loader.load()
            logger.info(f"Successfully loaded {len(documents)} documents from {directory_path}")
            return documents
        except Exception as e:
            logger.error(f"Error loading documents from {directory_path}: {str(e)}")
            raise
    
    def split_documents(self, documents):
        """Split documents into chunks for embedding."""
        logger.info(f"Splitting {len(documents)} documents into chunks")
        try:
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Created {len(chunks)} document chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error splitting documents: {str(e)}")
            raise
    
    def process_transcript(self, transcript_text: str, video_id: str) -> List:
        """Process a video transcript into optimally-sized chunks for Gemini."""
        logger.info(f"Processing transcript for video {video_id}, length: {len(transcript_text)} characters")
        
        if not transcript_text or not transcript_text.strip():
            logger.warning(f"Empty transcript for video {video_id}")
            return []
        
        try:
            # Create a document from the transcript
            doc = Document(
                page_content=transcript_text,
                metadata={
                    "video_id": video_id,
                    "source": "youtube_transcript"
                }
            )
            
            # Split into chunks optimized for Gemini
            chunks = self.text_splitter.split_documents([doc])
            
            # Add additional metadata to each chunk
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "video_id": video_id
                })
            
            logger.info(f"Created {len(chunks)} chunks for video {video_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing transcript for video {video_id}: {str(e)}")
            raise