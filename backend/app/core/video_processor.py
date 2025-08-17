# backend/app/core/video_processor.py
import os
import yt_dlp
import logging
import time
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)
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
        """Download audio and optional subtitles from a YouTube video with multiple fallback strategies."""
        video_id = self._extract_video_id(youtube_url)
        if not video_id:
            raise ValueError("Could not extract video ID from URL")
            
        # Create video-specific directory
        video_dir = os.path.join(self.output_dir, video_id)
        os.makedirs(video_dir, exist_ok=True)
        output_path = os.path.join(video_dir, video_id)
        
        logger.info(f"Attempting to download: {youtube_url}")
        
        # Strategy 1: Try with enhanced yt-dlp options
        strategies = [
            {
                'name': 'Enhanced yt-dlp with user agent',
                'opts': {
                    'format': 'bestaudio/best',
                    'outtmpl': output_path,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'cookiefile': 'cookies.txt',
                    'noplaylist': True,
                    'quiet': False,
                    'extract_flat': False,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    },
                    'extractor_retries': 3,
                    'fragment_retries': 3,
                }
            },
            {
                'name': 'Alternative format selection',
                'opts': {
                    'format': 'worstaudio/worst',
                    'outtmpl': output_path,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '128',
                    }],
                    'cookiefile': 'cookies.txt',
                    'noplaylist': True,
                    'quiet': False,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15',
                    },
                }
            },
            {
                'name': 'Basic download without postprocessing',
                'opts': {
                    'format': 'bestaudio',
                    'outtmpl': f"{output_path}.%(ext)s",
                    'cookiefile': 'cookies.txt',
                    'noplaylist': True,
                    'quiet': False,
                }
            }
        ]
        
        info = None
        last_error = None
        
        for i, strategy in enumerate(strategies):
            try:
                logger.info(f"Trying strategy {i+1}: {strategy['name']}")
                
                with yt_dlp.YoutubeDL(strategy['opts']) as ydl:
                    # Get video info first
                    if not info:
                        info = ydl.extract_info(youtube_url, download=False)
                        logger.info(f"Video info retrieved: {info.get('title', 'Unknown')}")
                    
                    # Attempt download
                    ydl.download([youtube_url])
                    
                    # Check if file was created
                    audio_path = f"{output_path}.mp3"
                    if not os.path.exists(audio_path):
                        # Check for other extensions
                        for ext in ['.webm', '.m4a', '.opus', '.wav']:
                            alt_path = f"{output_path}{ext}"
                            if os.path.exists(alt_path):
                                logger.info(f"Found audio file with extension {ext}, converting to mp3")
                                # Rename to .mp3 for consistency
                                os.rename(alt_path, audio_path)
                                break
                    
                    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                        logger.info(f"Download successful with strategy {i+1}")
                        break
                    else:
                        raise Exception("Audio file not created or empty")
                        
            except Exception as e:
                last_error = e
                logger.warning(f"Strategy {i+1} failed: {str(e)}")
                time.sleep(2)  # Wait before trying next strategy
                continue
        
        # Check final result
        audio_path = f"{output_path}.mp3"
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            error_msg = f"All download strategies failed. Last error: {last_error}"
            logger.error(error_msg)
            raise FileNotFoundError("Audio file was not downloaded successfully.")
        
        # Try to download subtitles separately
        subtitle_path = None
        try:
            subtitle_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'outtmpl': output_path,
                'cookiefile': 'cookies.txt',
            }
            
            with yt_dlp.YoutubeDL(subtitle_opts) as ydl:
                ydl.download([youtube_url])
                
            # Check for subtitle files
            for ext in ['.en.vtt', '.en.srt', '.vtt', '.srt']:
                candidate = f"{output_path}{ext}"
                if os.path.exists(candidate):
                    subtitle_path = candidate
                    logger.info(f"Subtitles downloaded: {subtitle_path}")
                    break
        except Exception as sub_err:
            logger.warning(f"Subtitle download failed: {sub_err}")
        
        result = {
            "video_id": video_id,
            "title": info.get('title', 'Unknown Title') if info else 'Unknown Title',
            "audio_path": audio_path,
            "duration": info.get('duration', 0) if info else 0
        }
        
        if subtitle_path:
            result["subtitle_path"] = subtitle_path
            
        logger.info(f"Download completed successfully: {result['title']}")
        return result

    def download_audio_with_fallback(self, youtube_url):
        """Wrapper method with additional error handling."""
        try:
            return self.download_audio(youtube_url)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Download failed: {error_msg}")
            
            # Provide more specific error messages
            if "HTTP Error 403" in error_msg:
                raise Exception("YouTube access denied (403 Forbidden). This video may be region-restricted or YouTube is blocking the download.")
            elif "Video unavailable" in error_msg:
                raise Exception("Video is unavailable or has been removed from YouTube.")
            elif "Private video" in error_msg:
                raise Exception("This is a private video and cannot be downloaded.")
            elif "Sign in to confirm your age" in error_msg:
                raise Exception("This video is age-restricted and requires sign-in to view.")
            else:
                raise Exception(f"Error downloading YouTube video: {error_msg}")