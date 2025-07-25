from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
from .logger import setup_logger

logger = setup_logger(__name__)

class VectorStore:
    """Manages document embeddings and vector store."""
    
    def __init__(self, embedding_model: str = "text-embedding-3-small"):
        """Initialize with specified embedding model."""
        logger.info(f"Initializing VectorStore with embedding model: {embedding_model}")
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.vector_store = None
    
    def create_vector_store(self, documents, store_name: str = "faiss_index"):
        """Create a new vector store from documents."""
        logger.info(f"Creating vector store '{store_name}' from {len(documents)} documents")
        try:
            # Ensure downloads directory exists
            os.makedirs("./downloads/vector_stores", exist_ok=True)
            store_path = os.path.join("./downloads/vector_stores", store_name)
            
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            logger.info(f"Vector store created successfully")
            self.save_vector_store(store_path)
            return self.vector_store
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            raise
    
    def load_vector_store(self, store_name: str = "faiss_index"):
        """Load an existing vector store."""
        # First try in downloads/vector_stores directory (preferred location)
        downloads_index_path = f"./downloads/vector_stores/{store_name}/index.faiss"
        downloads_docstore_path = f"./downloads/vector_stores/{store_name}/index.pkl"
        
        # For backward compatibility, check direct path
        index_direct_path = f"{store_name}/index.faiss"
        docstore_direct_path = f"{store_name}/index.pkl"
        
        # For backward compatibility, check old vector_stores directory
        index_path = f"vector_stores/{store_name}/index.faiss"
        docstore_path = f"vector_stores/{store_name}/index.pkl"
        
        logger.info(f"Attempting to load vector store: {store_name}")
        
        # First check downloads directory (preferred location)
        if os.path.exists(downloads_index_path) and os.path.exists(downloads_docstore_path):
            try:
                logger.info(f"Found vector store files in downloads/vector_stores directory")
                self.vector_store = FAISS.load_local(
                    f"./downloads/vector_stores/{store_name}", 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Vector store '{store_name}' loaded successfully from downloads directory")
                return self.vector_store
            except Exception as e:
                logger.error(f"Error loading vector store from downloads directory: {str(e)}")
                raise
        # Check if direct path exists (backward compatibility)
        elif os.path.exists(index_direct_path) and os.path.exists(docstore_direct_path):
            try:
                logger.info(f"Found vector store files directly in: {store_name}")
                self.vector_store = FAISS.load_local(
                    store_name, 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Vector store '{store_name}' loaded successfully")
                return self.vector_store
            except Exception as e:
                logger.error(f"Error loading vector store '{store_name}': {str(e)}")
                raise
        # Check old vector_stores directory (backward compatibility)
        elif os.path.exists(index_path) and os.path.exists(docstore_path):
            try:
                logger.info(f"Found vector store files in vector_stores directory")
                self.vector_store = FAISS.load_local(
                    f"vector_stores/{store_name}", 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Vector store '{store_name}' loaded successfully from vector_stores directory")
                return self.vector_store
            except Exception as e:
                logger.error(f"Error loading vector store from vector_stores directory: {str(e)}")
                raise
        else:
            logger.warning(f"Vector store files for '{store_name}' not found in any location")
            raise FileNotFoundError(f"Vector store files for {store_name} not found.")
    
    def save_vector_store(self, store_name: str = "faiss_index"):
        """Save the current vector store."""
        if self.vector_store:
            try:
                self.vector_store.save_local(store_name)
                logger.info(f"Vector store saved as {store_name}.faiss and {store_name}.pkl")
            except Exception as e:
                logger.error(f"Error saving vector store '{store_name}': {str(e)}")
                raise
        else:
            logger.warning("Cannot save vector store: No vector store initialized")
    
    def get_retriever(self, search_type: str = "similarity_score_threshold", 
                     k: int = 4, score_threshold: float = 0.7):
        """Get a retriever from the vector store with configurable search parameters."""
        if not self.vector_store:
            logger.error("Cannot create retriever: Vector store not initialized")
            raise ValueError("Vector store has not been initialized.")
        
        logger.info(f"Creating retriever with search_type={search_type}, k={k}, score_threshold={score_threshold}")
        search_kwargs = {"k": k}
        if search_type == "similarity_score_threshold":
            search_kwargs["score_threshold"] = score_threshold
            
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )