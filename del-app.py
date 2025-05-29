def main():
    # Create a test document if none exist
    import os
    if not os.path.exists("./documents"):
        os.makedirs("./documents")
    
    if not any(file.endswith('.txt') for file in os.listdir("./documents")):
        with open("./documents/sample.txt", "w") as f:
            f.write("This is a sample document for testing the RAG system.\n\n")
            f.write("It contains information about AI, machine learning, and natural language processing.\n\n")
            f.write("RAG (Retrieval-Augmented Generation) combines retrieval and generation for better answers.\n\n")
            f.write("Using vector databases helps find relevant information efficiently.")
    
    # Rest of your main function
    app = RAGApplication(docs_dir="./documents")
    app.initialize()
    
    # Create a session
    session_id = app.create_session(metadata={"user": "demo_user"})
    print(f"Created session: {session_id}")
    
    # Ask questions in the same session
    questions = [
        "What information can I find in the documents?",
        "Tell me more about the key topics mentioned.",
        "What are the main conclusions in the documents?"
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        response = app.ask(question, session_id)
        print(f"Answer: {response['answer']}")