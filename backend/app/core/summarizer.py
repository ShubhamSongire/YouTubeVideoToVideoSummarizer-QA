# backend/app/core/summarizer.py
import logging
import tiktoken
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.summarize import load_summarize_chain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class TextSummarizer:
    """Generates summaries of transcript text with intelligent chunking for different models."""
    
    def __init__(self, model_name="gemini-1.5-flash", temperature=0):
        # Use Gemini instead of OpenAI for consistency
        if "gemini" in model_name.lower():
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        else:
            # Fallback to OpenAI if needed
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
            
        self.model_name = model_name
        
        # Set token limits based on model
        self.token_limits = {
            "gpt-3.5-turbo": 4096,
            "gpt-4": 8192,
            "gemini-pro": 30000,
            "gemini-1.5-flash": 14000,  # Conservative limit for Gemini
            "gemini-1.5-pro": 30000
        }
        
        # Get the appropriate token limit
        self.max_tokens = self.token_limits.get(model_name, 3000)
        
        # Create text splitter with appropriate chunk size
        # Use ~70% of max tokens for chunk size to leave room for prompts
        chunk_size = int(self.max_tokens * 0.7)
        chunk_overlap = min(400, int(chunk_size * 0.1))
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info(f"TextSummarizer initialized for {model_name} with chunk_size={chunk_size}, max_tokens={self.max_tokens}")
    
    def estimate_tokens(self, text):
        """Estimate token count for text."""
        try:
            # Try to use tiktoken for more accurate estimation
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            return len(encoding.encode(text))
        except:
            # Fallback to rough estimation (1 token ≈ 4 characters)
            return len(text) // 4
    
    def summarize(self, text, summary_type="concise"):
        """Generate a summary of the provided text with intelligent chunking."""
        if not text or not text.strip():
            return "No content to summarize."
        
        logger.info(f"Starting summarization of text with {len(text)} characters")
        token_count = self.estimate_tokens(text)
        logger.info(f"Estimated token count: {token_count}")
        
        # Create document
        docs = [Document(page_content=text)]
        
        # Determine if we need to chunk the text
        if token_count > self.max_tokens * 0.8:  # Use 80% threshold for safety
            logger.info(f"Text exceeds token limit, splitting into chunks...")
            docs = self.text_splitter.split_documents(docs)
            logger.info(f"Split into {len(docs)} chunks")
            
            # For very large texts, use map-reduce approach
            if len(docs) > 1:
                return self._summarize_large_text(docs, summary_type)
        
        # For smaller texts, use direct summarization
        return self._summarize_single_chunk(docs[0].page_content, summary_type)
    
    def _summarize_single_chunk(self, text, summary_type="concise"):
        """Summarize a single chunk of text."""
        try:
            # Different prompt templates based on summary type
            if summary_type == "concise":
                chain = load_summarize_chain(self.llm, chain_type="stuff")
            elif summary_type == "bullet_points":
                chain = self._create_bullet_points_chain()
            else:
                chain = load_summarize_chain(self.llm, chain_type="stuff")
            
            # Generate summary
            docs = [Document(page_content=text)]
            summary = chain.run(docs)
            return summary
            
        except Exception as e:
            logger.error(f"Error in single chunk summarization: {str(e)}")
            # If there's still a token limit error, try to truncate
            if "context length" in str(e).lower() or "token" in str(e).lower():
                logger.warning("Token limit exceeded, trying with truncated text...")
                truncated_text = text[:int(len(text) * 0.5)]  # Use half the text
                return self._summarize_single_chunk(truncated_text, summary_type)
            raise e
    
    def _summarize_large_text(self, docs, summary_type="concise"):
        """Summarize large text using map-reduce approach."""
        try:
            logger.info(f"Using map-reduce approach for {len(docs)} chunks")
            
            # Step 1: Summarize each chunk individually
            chunk_summaries = []
            for i, doc in enumerate(docs):
                logger.info(f"Processing chunk {i+1}/{len(docs)}")
                try:
                    chunk_summary = self._summarize_single_chunk(doc.page_content, "concise")
                    chunk_summaries.append(chunk_summary)
                except Exception as e:
                    logger.warning(f"Failed to summarize chunk {i+1}: {str(e)}")
                    # Skip this chunk or use a truncated version
                    continue
            
            if not chunk_summaries:
                return "Unable to generate summary due to processing errors."
            
            # Step 2: Combine and summarize the chunk summaries
            combined_summary = "\n\n".join(chunk_summaries)
            logger.info(f"Combined summary length: {len(combined_summary)} characters")
            
            # If combined summary is still too long, recursively process it
            if self.estimate_tokens(combined_summary) > self.max_tokens * 0.8:
                logger.info("Combined summary still too long, processing recursively...")
                return self.summarize(combined_summary, summary_type)
            else:
                return self._summarize_single_chunk(combined_summary, summary_type)
                
        except Exception as e:
            logger.error(f"Error in large text summarization: {str(e)}")
            # Fallback: return the first successful chunk summary
            if chunk_summaries:
                return f"Partial summary (due to processing limitations): {chunk_summaries[0]}"
            return f"Unable to generate summary: {str(e)}"
    
    def _create_bullet_points_chain(self):
        """Create a chain specifically for bullet point summaries."""
        from langchain.prompts import PromptTemplate
        
        prompt_template = """Write a bullet-point summary of the following text:
        
        {text}
        
        BULLET-POINT SUMMARY:"""
        
        prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
        chain = load_summarize_chain(
            self.llm,
            chain_type="stuff",
            prompt=prompt
        )
        return chain