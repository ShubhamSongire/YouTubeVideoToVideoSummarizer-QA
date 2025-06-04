# backend/app/core/transcriber.py
import whisper
import os
import yt_dlp
import re
import logging
import tempfile

logger = logging.getLogger(__name__)

class Transcriber:
    """Handles speech-to-text conversion using either YouTube captions or Whisper."""
    
    def __init__(self, model_name="base"):
        """Initialize with specified Whisper model."""
        # Lazy load Whisper model only when needed
        self.model_name = model_name
        self._model = None
        
    @property
    def model(self):
        """Lazy load the Whisper model only when needed."""
        if self._model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self._model = whisper.load_model(self.model_name)
        return self._model
    
    def _get_video_id_from_path(self, audio_path):
        """Extract video ID from audio path."""
        # Example path: ./downloads/VIDEO_ID.mp3
        basename = os.path.basename(audio_path)
        video_id = basename.split('.')[0]  # Remove extension
        return video_id
        
    def _download_captions(self, video_id):
        """Try to download captions for a YouTube video."""
        logger.info(f"Attempting to download captions for video: {video_id}")
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        temp_dir = tempfile.mkdtemp()
        
        ydl_opts = {
            'writesubtitles': True,      # Write subtitles file
            'writeautomaticsub': True,   # Include auto-generated subs if no manual ones
            'subtitleslangs': ['en'],    # Download English subtitles
            'skip_download': True,       # Do NOT download video or audio
            'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Look for the caption file
                subtitle_path = None
                for file in os.listdir(temp_dir):
                    if file.endswith('.vtt') and video_id in file:
                        subtitle_path = os.path.join(temp_dir, file)
                        break
                
                if subtitle_path and os.path.exists(subtitle_path):
                    logger.info(f"Caption file found: {subtitle_path}")
                    return subtitle_path, info.get('title', 'Unknown')
                else:
                    logger.info("No caption file found")
                    return None, info.get('title', 'Unknown')
        except Exception as e:
            logger.warning(f"Error downloading captions: {str(e)}")
            return None, "Unknown"
    
    def _parse_vtt_captions(self, subtitle_path):
        """Parse VTT caption file and extract text and timestamps."""
        logger.info(f"Parsing VTT file: {subtitle_path}")
        
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract full text without timestamps
        cleaned_text = re.sub(r'(\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3})|WEBVTT|\n{2,}', '\n', content)
        full_text = cleaned_text.strip()
        
        # Extract segments with timestamps
        segments = []
        pattern = r'(\d{2}):(\d{2}):(\d{2})\.(\d{3}) --> (\d{2}):(\d{2}):(\d{2})\.(\d{3})\n(.*?)(?=\n\d{2}:\d{2}:\d{2}\.\d{3}|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            # Calculate start and end times in seconds
            start_h, start_m, start_s, start_ms, end_h, end_m, end_s, end_ms, text = match
            start_time = int(start_h) * 3600 + int(start_m) * 60 + int(start_s) + int(start_ms) / 1000
            end_time = int(end_h) * 3600 + int(end_m) * 60 + int(end_s) + int(end_ms) / 1000
            
            segments.append({
                "text": text.strip(),
                "start": start_time,
                "end": end_time
            })
            
        return {
            "full_text": full_text,
            "segments": segments
        }
    
    def _transcribe_with_whisper(self, audio_path):
        """Fall back to using Whisper for transcription."""
        logger.info(f"Using Whisper to transcribe: {audio_path}")
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Perform transcription with Whisper
        result = self.model.transcribe(audio_path)
        
        # Get full text
        full_text = result["text"]
        
        # Get segments with timestamps
        segments = []
        for segment in result["segments"]:
            segments.append({
                "text": segment["text"],
                "start": segment["start"],
                "end": segment["end"]
            })
        
        return {
            "full_text": full_text,
            "segments": segments
        }
    
    def transcribe(self, audio_path):
        """Transcribe audio, first trying YouTube captions, then falling back to Whisper."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        # Extract video ID from path
        video_id = self._get_video_id_from_path(audio_path)
        
        # Try to get captions first
        caption_path, title = self._download_captions(video_id)
        
        if caption_path:
            logger.info(f"Using YouTube captions for video: {video_id}")
            return self._parse_vtt_captions(caption_path)
        else:
            logger.info(f"No captions found, falling back to Whisper for video: {video_id}")
            return self._transcribe_with_whisper(audio_path)