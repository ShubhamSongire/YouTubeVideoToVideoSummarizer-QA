from langchain_core.runnables import RunnablePassthrough
from typing import Dict, List, Any, Optional
import os
from .logger import setup_logger

logger = setup_logger(__name__)

class RAGChain:
    """Main RAG chain that combines retrieval, history, and response generation."""
    
    def __init__(self, retriever, model_manager, session_manager):
        logger.info("Initializing RAG Chain")
        self.retriever = retriever
        self.model_manager = model_manager
        self.session_manager = session_manager
        self.chain = self._build_chain()
        logger.info("RAG Chain initialized successfully")
    
    def _build_chain(self):
        """Build the RAG chain with history and transcript awareness."""
        logger.info("Building RAG chain")
        try:
            prompt = self.model_manager.create_prompt_template()
            model = self.model_manager.llm
            
            def get_chat_history(input_dict):
                session_id = input_dict.get("session_id")
                logger.debug(f"Getting chat history for session_id: {session_id}")
                # Get chat history if session_id is provided
                if session_id:
                    return self.session_manager.get_messages(session_id)
                logger.debug("No session_id provided, returning empty history")
                return []
                
            def get_video_transcript(input_dict):
                """Get the full video transcript if available."""
                session_id = input_dict.get("session_id")
                if not session_id:
                    return None
                
                try:
                    session = self.session_manager.get_session(session_id)
                    metadata = session.get("metadata", {})
                    video_id = metadata.get("video_id")
                    
                    if video_id:
                        logger.info(f"Getting transcript for video ID: {video_id}")
                        transcript_path = f"./transcripts/{video_id}.txt"
                        if os.path.exists(transcript_path):
                            with open(transcript_path, "r") as f:
                                return f.read()
                except Exception as e:
                    logger.error(f"Error getting video transcript: {str(e)}")
                
                return None
            
            def get_context(input_dict):
                question = input_dict["question"]
                logger.info(f"Getting context for question: {question[:50]}...")
                docs = self.retriever.get_relevant_documents(question)
                
                # If no relevant docs found, try to use the full transcript
                if not docs:
                    logger.warning("No relevant documents found for context")
                    transcript = get_video_transcript(input_dict)
                    if transcript:
                        logger.info("Using full transcript as context since no relevant chunks were found")
                        return transcript
                    return "No relevant information found in the video transcript."
                    
                logger.info(f"Retrieved {len(docs)} documents for context")
                return "\n\n".join([doc.page_content for doc in docs])
            
            def get_docs(input_dict):
                question = input_dict["question"]
                logger.debug(f"Getting raw docs for question: {question[:50]}...")
                return self.retriever.get_relevant_documents(question)
            
            def get_answer(input_dict):
                logger.info("Generating answer from context and question")
                try:
                    prompt_value = prompt.invoke({
                        "context": input_dict["context"],
                        "chat_history": input_dict["chat_history"],
                        "question": input_dict["question"]
                    })
                    logger.debug("Prompt created, invoking model")
                    return model.invoke(prompt_value).content
                except Exception as e:
                    logger.error(f"Error generating answer: {str(e)}")
                    raise
            
            # Build chain with individual transformations
            logger.info("Assembling RAG chain components")
            rag_chain = (
                RunnablePassthrough()
                .assign(
                    context=get_context,
                    chat_history=get_chat_history,
                    docs=get_docs
                )
                .assign(answer=get_answer)
            )
            
            logger.info("RAG chain built successfully")
            return rag_chain
            
        except Exception as e:
            logger.error(f"Error building RAG chain: {str(e)}")
            raise
    
    def invoke(self, question: str, session_id: Optional[str] = None):
        """Process a question and return an answer."""
        logger.info(f"RAG Chain invoked with question: {question[:50]}...")
        logger.debug(f"Session ID: {session_id}")
        
        try:
            if session_id is None:
                logger.info("No session ID provided, creating new session")
                session_id = self.session_manager.create_session()
            
            # Add user question to history
            try:
                logger.debug("Adding user question to history")
                self.session_manager.add_user_message(session_id, question)
            except Exception as e:
                logger.error(f"Error adding user message: {str(e)}")
                # Continue processing even if history update fails
            
            # Get answer
            logger.info("Executing RAG chain")
            start_time = __import__('time').time()
            result = self.chain.invoke({
                "question": question,
                "session_id": session_id
            })
            elapsed_time = __import__('time').time() - start_time
            logger.info(f"RAG chain execution completed in {elapsed_time:.2f}s")
            
            # Add AI response to history
            try:
                logger.debug("Adding AI response to history")
                self.session_manager.add_ai_message(session_id, result["answer"])
            except Exception as e:
                logger.error(f"Error adding AI message: {str(e)}")
                # Continue processing even if history update fails
                
            # Ensure session_id is included in response
            result["session_id"] = session_id
            
            return result
        except Exception as e:
            logger.error(f"Error during RAG chain execution: {str(e)}")
            # Return minimal result with error information
            return {
                "session_id": session_id,
                "question": question,
                "answer": f"Error processing your question: {str(e)}",
                "context": [],
                "docs": [],
                "execution_time": 0
            }