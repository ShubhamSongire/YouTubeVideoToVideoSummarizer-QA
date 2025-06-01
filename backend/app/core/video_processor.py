# backend/app/core/video_processor.py
import os
import yt_dlp
import uuid
from urllib.parse import parse_qs, urlparse

class VideoProcessor:
    """Downloads and processes YouTube videos."""
    
    def __init__(self, output_dir="./downloads"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def _extract_video_id(self, youtube_url):
        """Extract the video ID from a YouTube URL."""
        parsed_url = urlparse(youtube_url)
        if parsed_url.netloc in ('youtu.be', 'www.youtu.be'):
            return parsed_url.path[1:]
        if parsed_url.netloc in ('youtube.com', 'www.youtube.com'):
            if parsed_url.path == '/watch':
                return parse_qs(parsed_url.query)['v'][0]
            if parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]
        return None
    
    def download_audio(self, youtube_url):
        """Download audio from YouTube video."""
        try:
            video_id = self._extract_video_id(youtube_url)
            if not video_id:
                raise ValueError("Could not extract video ID from URL")
            
            output_path = os.path.join(self.output_dir, f"{video_id}")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'noplaylist': True,
                'quiet': False,
                'extract_flat': False,
                'writesubtitles': True,      # Attempt to write subtitles
                'writeautomaticsub': True,   # Include auto-generated subs if no manual ones available
                'subtitleslangs': ['en'],    # Download English subtitles
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                title = info.get('title', 'Unknown Title')
                duration = info.get('duration', 0)
                
                # Now download the file and possibly subtitles
                ydl.download([youtube_url])
            
            # Add .mp3 extension for the return value since yt-dlp will add it
            output_path_with_ext = f"{output_path}.mp3"
            
            # Check if subtitles were downloaded
            subtitle_path = None
            for ext in ['.en.vtt', '.en.srt', '.vtt', '.srt']:
                potential_path = f"{output_path}{ext}"
                if os.path.exists(potential_path):
                    subtitle_path = potential_path
                    break
            
            result = {
                "video_id": video_id,
                "title": title,
                "audio_path": output_path_with_ext,
                "duration": duration
            }
            
            # Add subtitle path if found
            if subtitle_path:
                result["subtitle_path"] = subtitle_path
                
            return result
        except Exception as e:
            raise Exception(f"Error downloading YouTube video: {str(e)}")