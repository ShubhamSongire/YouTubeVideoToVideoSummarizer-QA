from langchain_core.runnables import RunnablePassthrough
from typing import Dict, List, Any, Optional

class RAGChain:
    """Main RAG chain that combines retrieval, history, and response generation."""
    
    def __init__(self, retriever, model_manager, session_manager):
        self.retriever = retriever
        self.model_manager = model_manager
        self.session_manager = session_manager
        self.chain = self._build_chain()
    
    def _build_chain(self):
        """Build the RAG chain with history awareness."""
        prompt = self.model_manager.create_prompt_template()
        model = self.model_manager.llm
        
        def get_chat_history(input_dict):
            session_id = input_dict.get("session_id")
            # Get chat history if session_id is provided
            if session_id:
                return self.session_manager.get_messages(session_id)
            return []
        
        def get_context(input_dict):
            question = input_dict["question"]
            docs = self.retriever.get_relevant_documents(question)
            if not docs:
                return "No relevant documents found."
            return "\n\n".join([doc.page_content for doc in docs])
        
        def get_docs(input_dict):
            question = input_dict["question"]
            return self.retriever.get_relevant_documents(question)
        
        def get_answer(input_dict):
            prompt_value = prompt.invoke({
                "context": input_dict["context"],
                "chat_history": input_dict["chat_history"],
                "question": input_dict["question"]
            })
            # Process prompt value and get response
            return model.invoke(prompt_value).content
        
        # Build chain with individual transformations
        rag_chain = (
            RunnablePassthrough()
            .assign(
                context=get_context,
                chat_history=get_chat_history,
                docs=get_docs
            )
            .assign(answer=get_answer)
        )
        
        return rag_chain
    
    def invoke(self, question: str, session_id: Optional[str] = None):
        """Process a question and return an answer."""
        if session_id is None:
            session_id = self.session_manager.create_session()
        
        # Add user question to history
        self.session_manager.add_user_message(session_id, question)
        
        # Get answer
        try:
            result = self.chain.invoke({
                "question": question,
                "session_id": session_id
            })
        except Exception as e:
            print(f"Error during RAG chain execution: {e}")
            result = {
                "answer": "I encountered an error while processing your question. Please try again.",
                "context": "Error in retrieval",
                "docs": []
            }
        
        # Add AI response to history
        self.session_manager.add_ai_message(session_id, result["answer"])
        
        return {
            "session_id": session_id,
            "question": question,
            "answer": result["answer"],
            "context": result["context"],
            "docs": result["docs"]
        }