from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
import uuid
from typing import Dict, List, Optional
import datetime

class SessionManager:
    """Manages chat sessions and history."""
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
    
    def create_session(self, session_id: Optional[str] = None, 
                      metadata: Optional[dict] = None) -> str:
        """Create a new chat session with optional metadata."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": ChatMessageHistory(),
                "created_at": datetime.datetime.now(),
                "metadata": metadata or {},
                "last_active": datetime.datetime.now()
            }
        
        return session_id
    
    def get_session(self, session_id: str):
        """Get a session by ID."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        self.sessions[session_id]["last_active"] = datetime.datetime.now()
        return self.sessions[session_id]
    
    def get_history(self, session_id: str) -> ChatMessageHistory:
        """Get chat history for a session."""
        session = self.get_session(session_id)
        return session["history"]
    
    def add_user_message(self, session_id: str, message: str):
        """Add a user message to the history."""
        history = self.get_history(session_id)
        history.add_user_message(message)
    
    def add_ai_message(self, session_id: str, message: str):
        """Add an AI message to the history."""
        history = self.get_history(session_id)
        history.add_ai_message(message)
    
    def get_messages(self, session_id: str):
        """Get all messages in the session."""
        history = self.get_history(session_id)
        return history.messages
    
    def list_sessions(self):
        """List all available sessions with metadata."""
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
            self.sessions[session_id]["history"] = ChatMessageHistory()
            
    def delete_session(self, session_id: str):
        """Delete a session completely."""
        if session_id in self.sessions:
            del self.sessions[session_id]