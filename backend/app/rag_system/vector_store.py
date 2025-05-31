from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os

class VectorStore:
    """Manages document embeddings and vector store."""
    
    def __init__(self, embedding_model: str = "text-embedding-3-small"):
        """Initialize with specified embedding model."""
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.vector_store = None
    
    def create_vector_store(self, documents, store_name: str = "faiss_index"):
        """Create a new vector store from documents."""
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        self.save_vector_store(store_name)
        return self.vector_store
    
    def load_vector_store(self, store_name: str = "faiss_index"):
        """Load an existing vector store."""
        index_path = f"{store_name}.faiss"
        docstore_path = f"{store_name}.pkl"
        
        if os.path.exists(index_path) and os.path.exists(docstore_path):
            self.vector_store = FAISS.load_local(store_name, self.embeddings)
            return self.vector_store
        else:
            raise FileNotFoundError(f"Vector store files for {store_name} not found.")
    
    def save_vector_store(self, store_name: str = "faiss_index"):
        """Save the current vector store."""
        if self.vector_store:
            self.vector_store.save_local(store_name)
            print(f"Vector store saved as {store_name}.faiss and {store_name}.pkl")
    
    def get_retriever(self, search_type: str = "similarity_score_threshold", 
                     k: int = 4, score_threshold: float = 0.7):
        """Get a retriever from the vector store with configurable search parameters."""
        if not self.vector_store:
            raise ValueError("Vector store has not been initialized.")
        
        search_kwargs = {"k": k}
        if search_type == "similarity_score_threshold":
            search_kwargs["score_threshold"] = score_threshold
            
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )