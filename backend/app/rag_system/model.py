from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from typing import Optional, List
import os
import threading
from dotenv import load_dotenv
from .logger import setup_logger

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)

class APIKeyManager:
    """Manages multiple API keys with round-robin rotation."""
    
    def __init__(self, api_keys: List[str]):
        """Initialize with a list of API keys.
        
        Args:
            api_keys: List of API keys to rotate through
        """
        self.api_keys = api_keys
        self.current_index = 0
        self._lock = threading.Lock()  # Thread-safe rotation
        
    def get_next_key(self) -> str:
        """Get the next API key in rotation.
        
        Returns:
            The next API key to use
        """
        with self._lock:
            key = self.api_keys[self.current_index]
            # Move to the next key for the next request
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            return key
            
    @classmethod
    def from_env_vars(cls, prefix: str = "GOOGLE_API_KEY") -> 'APIKeyManager':
        """Create an APIKeyManager from environment variables.
        
        Args:
            prefix: The prefix for environment variables containing API keys
                   Will look for GOOGLE_API_KEY, GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, etc.
        
        Returns:
            APIKeyManager instance with all found API keys
        """
        api_keys = []
        
        # Check for the base key
        base_key = os.getenv(prefix)
        if base_key:
            api_keys.append(base_key)
            
        # Check for numbered keys
        i = 1
        while True:
            key = os.getenv(f"{prefix}_{i}")
            if key:
                api_keys.append(key)
                i += 1
            else:
                # Stop when no more keys are found
                break
                
        if not api_keys:
            logger.warning(f"No API keys found with prefix {prefix}")
            
        return cls(api_keys)

class ModelManager:
    """Manages LLMs and prompt templates."""
    
    def __init__(self, model_name: str = "gemini-pro", temperature: float = 0):
        logger.info(f"Initializing ModelManager with model={model_name}, temperature={temperature}")
        self.model_name = model_name
        self.temperature = temperature
        
        # Create API key manager with all available keys
        self.key_manager = APIKeyManager.from_env_vars("GOOGLE_API_KEY")
        
        # Log number of API keys found
        num_keys = len(self.key_manager.api_keys)
        if num_keys == 0:
            logger.warning("No Google API keys found. Model will not function without keys.")
        else:
            logger.info(f"Found {num_keys} Google API keys for rotation")
        
        self._create_llm()
    
    def _create_llm(self):
        """Creates a new LLM instance with the next available API key."""
        try:
            if not self.key_manager.api_keys:
                logger.error("No Google API keys available")
                raise ValueError("No Google API keys available. Please provide at least one API key.")
                
            # Get next API key in rotation
            api_key = self.key_manager.get_next_key()
            
            # Create LLM with the key
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name, 
                temperature=self.temperature, 
                google_api_key=api_key
            )
            logger.info(f"LLM initialized successfully with API key ending in ...{api_key[-4:]}")
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            raise
    
    def get_llm(self):
        """Get an LLM instance with the next API key in rotation."""
        self._create_llm()
        return self.llm
    
    def create_prompt_template(self, system_template: Optional[str] = None):
        """Create a prompt template for RAG with configurable instructions."""
        logger.info("Creating prompt template")
        if system_template is None:
            logger.debug("Using default system template")
            system_template = """You are a helpful assistant that answers questions based on the provided video transcript and context.
            You're helping users understand the content of a YouTube video they're asking about.
            If the context doesn't contain the answer, say you don't know but try to be helpful.
            Don't make up information that's not in the context.
            Format your responses in a clear, readable way with markdown formatting where appropriate.
            If quoting from the context, make it clear by using quotation marks or blockquotes.
            Use the chat history to provide consistent responses."""
        
        template = ChatPromptTemplate.from_messages([
            ("system", system_template),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
            ("system", "Here is context information from the video transcript to help with the response: {context}")
        ])
        logger.info("Prompt template created successfully")
        return template