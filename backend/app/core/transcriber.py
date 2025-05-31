# backend/app/core/transcriber.py
import whisper
import os

class Transcriber:
    """Handles speech-to-text conversion."""
    
    def __init__(self, model_name="base"):
        """Initialize with specified Whisper model."""
        self.model = whisper.load_model(model_name)
    
    def transcribe(self, audio_path):
        """Transcribe audio file to text."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Perform transcription
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