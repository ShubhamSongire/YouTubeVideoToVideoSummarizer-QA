from setuptools import setup, find_packages

setup(
    name="youtube_video_qa",
    version="1.0.0",
    description="YouTube Video Question Answering with RAG",
    author="Shubham Songire",
    author_email="youremail@example.com",  # Replace with your email
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.110.0",
        "uvicorn>=0.30.0",
        "python-multipart>=0.0.9",
        "python-dotenv>=1.0.0",
        "langchain>=0.1.1",
        "langchain-openai>=0.0.5",
        "langchain-community>=0.0.19",
        "langchain-google-genai>=2.1.5",
        "google-generativeai>=0.3.2",
        "faiss-cpu>=1.11.0",
        "pydantic>=2.6.3",
        "protobuf>=4.25.8",
        "yt-dlp>=2023.12.30",
        "openai-whisper>=20231117",
        "streamlit>=1.32.0",
        "tiktoken>=0.6.0",
        "requests>=2.31.0",
        "gunicorn>=21.2.0",
    ],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
)
