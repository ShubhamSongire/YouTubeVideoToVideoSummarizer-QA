from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any

class DocumentProcessor:
    """Handles document loading and processing."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize document processor with configurable chunk parameters."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_documents(self, directory_path: str):
        """Load all text documents from a directory."""
        loader = DirectoryLoader(
            directory_path,
            glob="**/*.txt",
            loader_cls=TextLoader
        )
        documents = loader.load()
        print(f"Loaded {len(documents)} documents from {directory_path}")
        return documents
    
    def split_documents(self, documents):
        """Split documents into chunks for embedding."""
        chunks = self.text_splitter.split_documents(documents)
        print(f"Created {len(chunks)} document chunks")
        return chunks