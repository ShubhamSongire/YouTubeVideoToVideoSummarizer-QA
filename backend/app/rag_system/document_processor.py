from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any
from .logger import setup_logger

logger = setup_logger(__name__)

class DocumentProcessor:
    """Handles document loading and processing."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize document processor with configurable chunk parameters."""
        logger.info(f"Initializing DocumentProcessor with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
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