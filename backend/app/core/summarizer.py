# backend/app/core/summarizer.py
from langchain_openai import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

class TextSummarizer:
    """Generates summaries of transcript text."""
    
    def __init__(self, model_name="gpt-3.5-turbo", temperature=0):
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=400
        )
    
    def summarize(self, text, summary_type="concise"):
        """Generate a summary of the provided text."""
        # Create document
        docs = [Document(page_content=text)]
        
        # Split text if too long
        if len(text) > 3000:
            docs = self.text_splitter.split_documents(docs)
        
        # Different prompt templates based on summary type
        if summary_type == "concise":
            chain = load_summarize_chain(self.llm, chain_type="stuff")
        elif summary_type == "detailed":
            chain = load_summarize_chain(self.llm, chain_type="map_reduce")
        elif summary_type == "bullet_points":
            # Custom chain for bullet points
            chain = self._create_bullet_points_chain()
        else:
            chain = load_summarize_chain(self.llm, chain_type="stuff")
        
        # Generate summary
        summary = chain.run(docs)
        return summary
    
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