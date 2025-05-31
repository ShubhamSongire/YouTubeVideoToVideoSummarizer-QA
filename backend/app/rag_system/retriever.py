from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain_core.documents import Document
from typing import List, Dict

class EnhancedRetriever:
    """Creates enhanced retrieval mechanisms."""
    
    def __init__(self, base_retriever, relevance_threshold: float = 0.3):  # Lowered from 0.7 to 0.3
        self.base_retriever = base_retriever
        self.relevance_threshold = relevance_threshold
        self.retriever = base_retriever
        
    def setup_contextual_compression(self, embeddings):
        """Create a retriever with contextual compression."""
        embeddings_filter = EmbeddingsFilter(
            embeddings=embeddings,
            similarity_threshold=self.relevance_threshold
        )
        
        self.retriever = ContextualCompressionRetriever(
            base_compressor=embeddings_filter,
            base_retriever=self.base_retriever
        )
        return self.retriever
    
    def setup_time_weighted(self, decay_rate: float = 0.01):
        """Create a time-weighted retriever that prioritizes recent documents."""
        self.retriever = TimeWeightedRetriever(
            retriever=self.base_retriever,
            decay_rate=decay_rate,
            k=4
        ) 
        return self.retriever
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """Get relevant documents for a query."""
        return self.retriever.get_relevant_documents(query)