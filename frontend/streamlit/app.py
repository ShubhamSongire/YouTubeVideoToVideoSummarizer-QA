# frontend/streamlit/app.py
import streamlit as st
import requests
import time
import json

# API endpoint
API_URL = "http://localhost:8000"

st.set_page_config(page_title="YouTube Video QA", layout="wide")

st.title("🎥 YouTube Video QA System")

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

# Main content area
tab1, tab2, tab3 = st.tabs(["📝 Summary", "❓ Q&A", "📄 Transcript"])

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
                        "question": question,
                        "session_id": st.session_state.session_id
                    }
                    
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