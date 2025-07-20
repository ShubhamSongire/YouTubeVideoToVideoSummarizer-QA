# backend/app/core/video_processor.py
import os
import yt_dlp
import time
import random
from urllib.parse import parse_qs, urlparse

class VideoProcessor:
    """Downloads and processes YouTube videos."""
    def __init__(self, output_dir="./downloads"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.is_cloud_environment = self._detect_cloud_environment()
        
    def _detect_cloud_environment(self):
        """Detect if running in a cloud environment."""
        cloud_indicators = [
            'RENDER',  # Render.com
            'HEROKU',  # Heroku
            'VERCEL',  # Vercel
            'RAILWAY', # Railway
            'FLY',     # Fly.io
            'GOOGLE_CLOUD_PROJECT',  # Google Cloud
            'AWS_LAMBDA_FUNCTION_NAME'  # AWS Lambda
        ]
        
        for indicator in cloud_indicators:
            if os.environ.get(indicator):
                print(f"Cloud environment detected: {indicator}")
                return True
                
        # Check for common cloud IP ranges or hostnames
        hostname = os.environ.get('HOSTNAME', '')
        if any(cloud in hostname.lower() for cloud in ['render', 'heroku', 'railway']):
            print(f"Cloud environment detected from hostname: {hostname}")
            return True
            
        return False
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
            # Add delay for cloud environments to avoid rate limiting
            if self.is_cloud_environment:
                delay = random.uniform(1, 3)
                print(f"Cloud environment detected. Adding {delay:.1f}s delay to avoid rate limiting...")
                time.sleep(delay)
            
            video_id = self._extract_video_id(youtube_url)
            if not video_id:
                raise ValueError("Could not extract video ID from URL")

            output_path = os.path.join(self.output_dir, video_id)
            
            # Dynamic configuration based on environment
            sleep_interval = 2 if self.is_cloud_environment else 0
            max_sleep = 5 if self.is_cloud_environment else 1
            
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
                
                # Cloud deployment optimizations
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'referer': 'https://www.youtube.com/',
                'sleep_interval': sleep_interval,
                'max_sleep_interval': max_sleep,
                
                # Use mobile client to avoid some restrictions
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'skip': ['dash', 'hls']
                    }
                },
                
                # Retry configuration
                'retries': 5,
                'fragment_retries': 5,
                'retry_sleep_functions': {'http': lambda n: min(2 ** n, 10)},
                
                # Additional headers to appear more like a regular browser
                'http_headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            }
            info = None
            download_success = False
            
            # Strategy 1: Try with subtitles and full features
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=False)
                    title = info.get('title', 'Unknown Title')
                    duration = info.get('duration', 0)
                    print(f"Downloading audio + subtitles for: {title}")
                    ydl.download([youtube_url])
                    download_success = True
                    print("Strategy 1: Full download complete.")
            except Exception as sub_err:
                print(f"Strategy 1 failed: {sub_err}. Trying fallback strategies...")
                
                # Strategy 2: Audio only with reduced features
                try:
                    fallback_opts = ydl_opts.copy()
                    fallback_opts.update({
                        'writesubtitles': False,
                        'writeautomaticsub': False,
                        'extractor_args': {'youtube': {'player_client': ['android']}},
                        'format': 'worst[ext=m4a]/worst'  # Try lower quality first
                    })
                    
                    with yt_dlp.YoutubeDL(fallback_opts) as ydl_audio:
                        if not info:  # Get info if we don't have it yet
                            info = ydl_audio.extract_info(youtube_url, download=False)
                        ydl_audio.download([youtube_url])
                        download_success = True
                        print("Strategy 2: Audio-only download complete.")
                        
                except Exception as fallback_err:
                    print(f"Strategy 2 failed: {fallback_err}. Trying final strategy...")
                    
                    # Strategy 3: Minimal configuration
                    try:
                        minimal_opts = {
                            'format': 'worst',
                            'outtmpl': output_path,
                            'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '128',  # Lower quality
                            }],
                            'noplaylist': True,
                            'quiet': True,
                            'no_warnings': True,
                            'ignoreerrors': True,
                            'user_agent': 'yt-dlp/2023.12.30',
                            'extractor_args': {'youtube': {'player_client': ['android']}}
                        }
                        
                        with yt_dlp.YoutubeDL(minimal_opts) as ydl_minimal:
                            if not info:
                                info = ydl_minimal.extract_info(youtube_url, download=False)
                            ydl_minimal.download([youtube_url])
                            download_success = True
                            print("Strategy 3: Minimal download complete.")
                            
                    except Exception as final_err:
                        print(f"All download strategies failed. Final error: {final_err}")
                        raise Exception(f"Unable to download video after trying all strategies. Last error: {final_err}")
            
            if not download_success:
                raise Exception("Download failed with all attempted strategies")
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
            error_msg = str(e).lower()
            
            # Provide specific guidance based on error type
            if '429' in error_msg or 'too many requests' in error_msg:
                detailed_error = (
                    f"Rate limiting detected on cloud platform. "
                    f"This is common with shared cloud IPs. "
                    f"Original error: {str(e)}"
                )
            elif 'this content isn\'t available' in error_msg or 'video unavailable' in error_msg:
                detailed_error = (
                    f"Content geo-blocked or unavailable from cloud server location. "
                    f"The video may be restricted in the cloud server's region. "
                    f"Original error: {str(e)}"
                )
            elif 'http error 403' in error_msg:
                detailed_error = (
                    f"Access forbidden - YouTube detected automated access. "
                    f"This is common with cloud deployments. "
                    f"Original error: {str(e)}"
                )
            else:
                detailed_error = f"Error downloading YouTube video: {str(e)}"
                
            # Add environment context to error message
            if self.is_cloud_environment:
                detailed_error += (
                    f"\n\nCloud Environment Detected: This error is likely due to "
                    f"YouTube's restrictions on cloud/server IPs. Consider:\n"
                    f"1. Using a proxy service\n"
                    f"2. Implementing request caching\n"
                    f"3. Using alternative video sources"
                )
                
            raise Exception(detailed_error)