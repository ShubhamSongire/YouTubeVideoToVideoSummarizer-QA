from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers import TimeWeightedVectorStoreRetriever  
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain_core.documents import Document
from typing import List, Dict
from .logger import setup_logger

logger = setup_logger(__name__)

class EnhancedRetriever:
    """Creates enhanced retrieval mechanisms."""
    
    def __init__(self, base_retriever, relevance_threshold: float = 0.3):
        logger.info(f"Initializing EnhancedRetriever with threshold={relevance_threshold}")
        self.base_retriever = base_retriever
        self.relevance_threshold = relevance_threshold
        self.retriever = base_retriever
        
    def setup_contextual_compression(self, embeddings):
        """Create a retriever with contextual compression."""
        logger.info("Setting up contextual compression retriever")
        try:
            embeddings_filter = EmbeddingsFilter(
                embeddings=embeddings,
                similarity_threshold=self.relevance_threshold
            )
            
            self.retriever = ContextualCompressionRetriever(
                base_compressor=embeddings_filter,
                base_retriever=self.base_retriever
            )
            logger.info("Contextual compression retriever created successfully")
            return self.retriever
        except Exception as e:
            logger.error(f"Error setting up contextual compression: {str(e)}")
            raise
    
    def setup_time_weighted(self, decay_rate: float = 0.01):
        """Create a time-weighted retriever that prioritizes recent documents."""
        logger.info(f"Setting up time-weighted retriever with decay_rate={decay_rate}")
        try:
            if hasattr(self.base_retriever, 'vectorstore'):
                vector_store = self.base_retriever.vectorstore
                self.retriever = TimeWeightedVectorStoreRetriever(
                    vectorstore=vector_store,
                    decay_rate=decay_rate,
                    k=4
                )
                logger.info("Time-weighted retriever created successfully")
                return self.retriever
            else:
                logger.error("Base retriever has no vectorstore attribute")
                raise ValueError("Base retriever does not have an accessible vectorstore")
        except Exception as e:
            logger.error(f"Error setting up time-weighted retriever: {str(e)}")
            raise
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """Get relevant documents for a query."""
        logger.info(f"Retrieving documents for query: {query[:50]}...")
        try:
            docs = self.retriever.get_relevant_documents(query)
            logger.info(f"Retrieved {len(docs)} documents")
            if len(docs) == 0:
                logger.warning("No relevant documents found")
            return docs
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            raise