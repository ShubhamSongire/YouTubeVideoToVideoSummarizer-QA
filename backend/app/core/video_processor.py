# backend/app/core/video_processor.py
import os
import yt_dlp
from urllib.parse import parse_qs, urlparse
class VideoProcessor:
    """Downloads and processes YouTube videos."""
    def __init__(self, output_dir="./downloads"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    def _extract_video_id(self, youtube_url):
        """Extract the video ID from a YouTube URL."""
        parsed_url = urlparse(youtube_url)
        if parsed_url.netloc in ('youtu.be', 'www.youtu.be'):
            return parsed_url.path[1:]
        if parsed_url.netloc in ('youtube.com', 'www.youtube.com'):
            if parsed_url.path == '/watch':
                query_params = parse_qs(parsed_url.query)
                if 'v' in query_params and query_params['v']:
                    return query_params['v'][0]
            if parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]
        return None
    def download_audio(self, youtube_url):
        """Download audio and optional subtitles from a YouTube video."""
        try:
            video_id = self._extract_video_id(youtube_url)
            if not video_id:
                raise ValueError("Could not extract video ID from URL")
            output_path = os.path.join(self.output_dir, video_id)
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
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'ignoreerrors': True,
            }
            info = None
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=False)
                    title = info.get('title', 'Unknown Title')
                    duration = info.get('duration', 0)
                    print(f"Downloading audio + subtitles for: {title}")
                    ydl.download([youtube_url])
                    print("Initial download complete.")
            except Exception as sub_err:
                print(f"Warning: Subtitles download failed: {sub_err}. Retrying audio only...")
                ydl_opts['writesubtitles'] = False
                ydl_opts['writeautomaticsub'] = False
                with yt_dlp.YoutubeDL(ydl_opts) as ydl_audio:
                    ydl_audio.download([youtube_url])
                    print("Audio-only download complete.")
            # Final .mp3 file path
            audio_path = f"{output_path}.mp3"
            if not os.path.exists(audio_path):
                raise FileNotFoundError("Audio file was not downloaded successfully.")
            # Check for subtitle file
            subtitle_path = None
            for ext in ['.en.vtt', '.en.srt', '.vtt', '.srt']:
                candidate = f"{output_path}{ext}"
                if os.path.exists(candidate):
                    subtitle_path = candidate
                    break
            result = {
                "video_id": video_id,
                "title": info.get('title', 'Unknown Title') if info else 'Unknown Title',
                "audio_path": audio_path,
                "duration": info.get('duration', 0) if info else 0
            }
            if subtitle_path:
                result["subtitle_path"] = subtitle_path
            return result
        except Exception as e:
            raise Exception(f"Error downloading YouTube video: {str(e)}")