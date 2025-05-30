from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from typing import Optional
from .logger import setup_logger

logger = setup_logger(__name__)

class ModelManager:
    """Manages LLMs and prompt templates."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0):
        logger.info(f"Initializing ModelManager with model={model_name}, temperature={temperature}")
        self.model_name = model_name
        self.temperature = temperature
        try:
            self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
            logger.info("LLM initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            raise
    
    def create_prompt_template(self, system_template: Optional[str] = None):
        """Create a prompt template for RAG with configurable instructions."""
        logger.info("Creating prompt template")
        if system_template is None:
            logger.debug("Using default system template")
            system_template = """You are a helpful assistant that answers questions based on the provided context.
            If the context doesn't contain the answer, say you don't know but try to be helpful.
            Don't make up information that's not in the context.
            Format your responses in a clear, readable way with markdown formatting where appropriate.
            If quoting from the context, make it clear by using quotation marks or blockquotes."""
        
        template = ChatPromptTemplate.from_messages([
            ("system", system_template),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
            ("system", "Here is context information to help with the response: {context}")
        ])
        logger.info("Prompt template created successfully")
        return template