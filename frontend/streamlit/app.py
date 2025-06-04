# frontend/streamlit/app.py
import streamlit as st
import requests
import time
import json
import os
from requests.exceptions import ConnectionError, Timeout

# API endpoint - use environment variable if available, otherwise default to localhost
API_URL = os.environ.get("API_URL", "http://localhost:8080")

st.set_page_config(page_title="YouTube Video QA System", layout="wide")

# Check if API is available
api_available = False
api_version = "unknown"
try:
    response = requests.get(f"{API_URL}/", timeout=5)
    if response.status_code == 200:
        api_available = True
        api_data = response.json()
        api_version = api_data.get("service", "YouTube Video QA API")
except (ConnectionError, Timeout):
    api_available = False

st.title("🎥 YouTube Video QA System")

# Display API status
if api_available:
    st.success(f"✅ Connected to backend API: {api_version}")
else:
    st.error(f"❌ Backend API not available at {API_URL}. Some features may not work.")

# Session state initialization
if 'processing_id' not in st.session_state:
    st.session_state.processing_id = None
if 'video_id' not in st.session_state:
    st.session_state.video_id = None
if 'video_title' not in st.session_state:
    st.session_state.video_title = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar for URL input
with st.sidebar:
    st.header("Video Input")
    youtube_url = st.text_input("Enter YouTube URL:")
    process_btn = st.button("Process Video")
    
    if process_btn and youtube_url:
        with st.spinner("Starting video processing..."):
            try:
                # Call API to process video
                response = requests.post(
                    f"{API_URL}/process-video",
                    json={"youtube_url": youtube_url}
                )
                data = response.json()
                
                # Save processing ID
                st.session_state.processing_id = data["processing_id"]
                st.success("Video processing started!")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Status check section
    if st.session_state.processing_id:
        st.subheader("Processing Status")
        check_status = st.button("Check Status")
        
        if check_status:
            try:
                response = requests.get(f"{API_URL}/video/{st.session_state.processing_id}")
                status_data = response.json()
                
                # Update session state if completed
                if status_data["status"] == "completed":
                    st.session_state.video_id = status_data["video_id"]
                    st.session_state.video_title = status_data["title"]
                    
                # Display status
                st.json(status_data["steps"])
                
                if status_data["status"] == "completed":
                    st.success("Processing completed!")
                elif status_data["status"] == "failed":
                    st.error(f"Processing failed: {status_data.get('error', 'Unknown error')}")
                else:
                    st.info(f"Current status: {status_data['status']}")
                    
            except Exception as e:
                st.error(f"Error checking status: {str(e)}")
    
    # Cleanup section
    st.subheader("Cleanup")
    
    # Button to clean up current video
    if st.session_state.video_id:
        cleanup_video_btn = st.button("Clean Current Video")
        if cleanup_video_btn:
            with st.spinner("Cleaning up video files..."):
                try:
                    # Call API to clean up current video
                    response = requests.post(
                        f"{API_URL}/cleanup/video",
                        json={
                            "video_id": st.session_state.video_id,
                            "clear_memory": True
                        }
                    )
                    if response.status_code == 200:
                        # Reset session state
                        st.session_state.processing_id = None
                        st.session_state.video_id = None
                        st.session_state.video_title = None
                        st.session_state.session_id = None
                        st.session_state.chat_history = []
                        st.success("Video cleaned up successfully!")
                        # Force page reload to reset UI
                        st.experimental_rerun()
                    else:
                        st.error(f"Error cleaning up video: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                
    # Button to clean up all videos
    with st.expander("Advanced Cleanup"):
        st.warning("This will delete all processed videos and reset the application.")
        cleanup_all_btn = st.button("Clean All Videos")
        if cleanup_all_btn:
            with st.spinner("Cleaning up all files..."):
                try:
                    # Call API to clean up all videos
                    response = requests.post(
                        f"{API_URL}/cleanup/all",
                        json={"clear_memory": True}
                    )
                    if response.status_code == 200:
                        # Reset session state
                        st.session_state.processing_id = None
                        st.session_state.video_id = None
                        st.session_state.video_title = None
                        st.session_state.session_id = None
                        st.session_state.chat_history = []
                        st.success("All videos cleaned up successfully!")
                        # Force page reload to reset UI
                        st.experimental_rerun()
                    else:
                        st.error(f"Error cleaning up videos: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["📝 Summary", "❓ Q&A", "📄 Transcript", "🧹 Cleanup"])

# Summary tab
with tab1:
    st.header("Video Summary")
    
    if st.session_state.processing_id and st.session_state.video_id:
        try:
            # Get summary
            response = requests.get(f"{API_URL}/video/{st.session_state.processing_id}/summary")
            
            if response.status_code == 200:
                summary_data = response.json()
                
                # Display video info
                st.subheader(summary_data["title"])
                
                # Display summary
                st.markdown("### Summary")
                st.write(summary_data["summary"])
            else:
                st.info("Summary not available yet. Please wait for processing to complete.")
                
        except Exception as e:
            st.error(f"Error retrieving summary: {str(e)}")
    else:
        st.info("Process a video to see its summary.")

# Q&A tab
with tab2:
    st.header("Ask Questions")
    
    if st.session_state.video_id:
        # Display chat history
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])
        
        # Question input
        question = st.chat_input("Ask a question about the video:")
        
        if question:
            # Add user question to chat history
            st.session_state.chat_history.append({
                "role": "user",
                "content": question
            })
            
            # Display user question
            st.chat_message("user").write(question)
            
            # Call API to get answer
            with st.spinner("Thinking..."):
                try:
                    payload = {
                        "video_id": st.session_state.video_id,
                        "question": question
                    }
                    
                    # Only add session_id to payload if it exists
                    if st.session_state.session_id:
                        payload["session_id"] = st.session_state.session_id
                    
                    response = requests.post(f"{API_URL}/ask", json=payload)
                    answer_data = response.json()
                    
                    # Save session ID if it's new
                    if st.session_state.session_id is None:
                        st.session_state.session_id = answer_data["session_id"]
                    
                    # Add answer to chat history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer_data["answer"]
                    })
                    
                    # Display answer
                    st.chat_message("assistant").write(answer_data["answer"])
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.info("Process a video first to ask questions about it.")

# Transcript tab
with tab3:
    st.header("Full Transcript")
    
    if st.session_state.processing_id and st.session_state.video_id:
        try:
            # Get transcript
            response = requests.get(f"{API_URL}/video/{st.session_state.processing_id}/transcript")
            
            if response.status_code == 200:
                transcript_data = response.json()
                
                # Display video info
                st.subheader(transcript_data["title"])
                
                # Display transcription source if available
                if "transcription_source" in transcript_data:
                    source = transcript_data["transcription_source"]
                    if source == "captions":
                        st.success("✅ Using YouTube's captions (faster and more accurate)")
                    elif source == "whisper":
                        st.info("🎙️ Using Whisper speech-to-text (AI transcription)")
                    else:
                        st.info("📝 Transcript source: unknown")
                
                # Add search/filter functionality
                search_term = st.text_input("Search within transcript:", key="transcript_search")
                
                # Display transcript
                st.markdown("### Transcript")
                
                # Get the transcript text
                transcript_text = transcript_data["transcript"]
                
                # Filter by search term if provided
                if search_term:
                    # Highlight search terms
                    highlighted_text = transcript_text.replace(
                        search_term, 
                        f"**{search_term}**"
                    )
                    st.markdown(highlighted_text)
                else:
                    st.markdown(transcript_text)
                
                # Add download button
                st.download_button(
                    label="Download Transcript",
                    data=transcript_text,
                    file_name=f"{st.session_state.video_id}_transcript.txt",
                    mime="text/plain"
                )
                
                # Display segments if available
                if "segments" in transcript_data:
                    with st.expander("Show Timestamped Segments"):
                        segments = transcript_data["segments"]
                        for i, segment in enumerate(segments):
                            st.markdown(f"**[{segment['start']:.2f}s - {segment['end']:.2f}s]**: {segment['text']}")
                
            else:
                st.info("Transcript not available yet. Please wait for processing to complete.")
                
        except Exception as e:
            st.error(f"Error retrieving transcript: {str(e)}")
    else:
        st.info("Process a video to see its transcript.")

# Cleanup tab
with tab4:
    st.header("Cleanup Options")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.session_state.video_id:
            # Current video info
            st.subheader("Current Video")
            st.info(f"**Video ID:** {st.session_state.video_id}")
            if st.session_state.video_title:
                st.info(f"**Title:** {st.session_state.video_title}")
            
            # Cleanup current video section
            st.markdown("### Clean Current Video")
            st.write("""
            This will remove all files related to the current video from the server, including:
            - Audio files
            - Transcript files
            - Vector store files (used for answering questions)
            
            Your chat history will also be reset.
            """)
            cleanup_video_btn = st.button("Clean Current Video", key="cleanup_tab_btn", 
                                        help="Delete files for only the current video")
            
            if cleanup_video_btn:
                with st.spinner("Cleaning up video files..."):
                    try:
                        # Call API to clean up current video
                        response = requests.post(
                            f"{API_URL}/cleanup/video",
                            json={
                                "video_id": st.session_state.video_id,
                                "clear_memory": True
                            },
                            timeout=30  # Add timeout for better error handling
                        )
                        if response.status_code == 200:
                            cleanup_data = response.json()
                            st.success(f"Video cleaned up successfully! Deleted {sum(cleanup_data['deleted'].values())} files.")
                            
                            # Reset session state
                            st.session_state.processing_id = None
                            st.session_state.video_id = None
                            st.session_state.video_title = None
                            st.session_state.chat_history = []
                            st.session_state.session_id = None
                            
                            # Display notification to refresh
                            st.info("Please refresh the page to process another video.")
                            st.button("Refresh Page", on_click=lambda: st.experimental_rerun())
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection error: {str(e)}")
                    except Exception as e:
                        st.error(f"Error during cleanup: {str(e)}")
                        st.session_state.video_title = None
                        st.session_state.session_id = None
                        st.session_state.chat_history = []
                        
                        # Force page reload to reset UI
                        st.experimental_rerun()
                    else:
                        st.error(f"Error cleaning up video: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.info("Process a video first to see cleanup options.")
    
    # Global cleanup section
    st.markdown("### Advanced Cleanup Options")
    with st.expander("Clean All Videos"):
        st.warning("""
        ⚠️ **Warning:** This will delete all processed videos and related files from the server.
        All your conversations and transcripts will be lost.
        """)
        
        st.write("""
        Use this option to free up space on the server or to troubleshoot any issues.
        All downloaded files, transcripts, and vector stores will be removed.
        """)
        
        cleanup_all_confirm = st.checkbox("I understand that all data will be deleted")
        cleanup_all_btn = st.button("Clean All Videos", disabled=not cleanup_all_confirm, key="cleanup_all_tab_btn")
        
        if cleanup_all_btn:
            with st.spinner("Cleaning up all files..."):
                try:
                    # Call API to clean up all videos
                    response = requests.post(
                        f"{API_URL}/cleanup/all",
                        json={"clear_memory": True}
                    )
                    if response.status_code == 200:
                        cleanup_data = response.json()
                        st.success(f"All videos cleaned up successfully! Deleted {sum(cleanup_data['deleted'].values())} files.")
                        
                        # Reset session state
                        st.session_state.processing_id = None
                        st.session_state.video_id = None
                        st.session_state.video_title = None
                        st.session_state.session_id = None
                        st.session_state.chat_history = []
                        
                        # Force page reload to reset UI
                        st.experimental_rerun()
                    else:
                        st.error(f"Error cleaning up videos: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")