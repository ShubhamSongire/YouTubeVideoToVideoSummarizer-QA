from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
import uuid
from typing import Dict, List, Optional
import datetime
from .logger import setup_logger

logger = setup_logger(__name__)

class SessionManager:
    """Manages chat sessions and history."""
    
    def __init__(self):
        logger.info("Initializing SessionManager")
        self.sessions: Dict[str, dict] = {}
    
    def create_session(self, session_id: Optional[str] = None, 
                      metadata: Optional[dict] = None) -> str:
        """Create a new chat session with optional metadata."""
        if session_id is None:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session ID: {session_id}")
        
        if session_id not in self.sessions:
            logger.info(f"Creating new session: {session_id} with metadata: {metadata}")
            self.sessions[session_id] = {
                "history": ChatMessageHistory(),
                "created_at": datetime.datetime.now(),
                "metadata": metadata or {},
                "last_active": datetime.datetime.now()
            }
        else:
            logger.info(f"Session {session_id} already exists, returning existing session")
        
        return session_id
    
    def get_session(self, session_id: str):
        """Get a session by ID."""
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found")
            raise ValueError(f"Session {session_id} not found")
        
        logger.debug(f"Accessing session {session_id}")
        self.sessions[session_id]["last_active"] = datetime.datetime.now()
        return self.sessions[session_id]
    
    def get_history(self, session_id: str) -> ChatMessageHistory:
        """Get chat history for a session."""
        logger.debug(f"Getting history for session {session_id}")
        session = self.get_session(session_id)
        return session["history"]
    
    def add_user_message(self, session_id: str, message: str):
        """Add a user message to the history."""
        logger.info(f"Adding user message to session {session_id}")
        history = self.get_history(session_id)
        history.add_user_message(message)
    
    def add_ai_message(self, session_id: str, message: str):
        """Add an AI message to the history."""
        logger.info(f"Adding AI message to session {session_id}")
        history = self.get_history(session_id)
        history.add_ai_message(message)
    
    def get_messages(self, session_id: str):
        """Get all messages in the session."""
        logger.debug(f"Getting all messages from session {session_id}")
        history = self.get_history(session_id)
        return history.messages
    
    def list_sessions(self):
        """List all available sessions with metadata."""
        logger.info(f"Listing all sessions. Total count: {len(self.sessions)}")
        return {
            session_id: {
                "created_at": session["created_at"],
                "last_active": session["last_active"],
                "metadata": session["metadata"],
                "message_count": len(session["history"].messages)
            }
            for session_id, session in self.sessions.items()
        }
    
    def clear_session(self, session_id: str):
        """Clear a session's history."""
        if session_id in self.sessions:
            logger.info(f"Clearing history for session {session_id}")
            self.sessions[session_id]["history"] = ChatMessageHistory()
        else:
            logger.warning(f"Cannot clear session {session_id}: Session not found")
            
    def delete_session(self, session_id: str):
        """Delete a session completely."""
        if session_id in self.sessions:
            logger.info(f"Deleting session {session_id}")
            del self.sessions[session_id]
        else:
            logger.warning(f"Cannot delete session {session_id}: Session not found")