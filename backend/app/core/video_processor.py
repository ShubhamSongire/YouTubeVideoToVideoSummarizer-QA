# backend/app/core/video_processor.py
from pytube import YouTube
import os
import uuid

class VideoProcessor:
    """Downloads and processes YouTube videos."""
    
    def __init__(self, output_dir="./downloads"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def download_audio(self, youtube_url):
        """Download audio from YouTube video."""
        try:
            yt = YouTube(youtube_url)
            video_id = yt.video_id
            title = yt.title
            
            # Get audio stream
            audio_stream = yt.streams.filter(only_audio=True).first()
            
            # Download audio
            output_path = os.path.join(self.output_dir, f"{video_id}.mp4")
            audio_stream.download(output_path=self.output_dir, filename=f"{video_id}.mp4")
            
            return {
                "video_id": video_id,
                "title": title,
                "audio_path": output_path,
                "duration": yt.length
            }
        except Exception as e:
            raise Exception(f"Error downloading YouTube video: {str(e)}")