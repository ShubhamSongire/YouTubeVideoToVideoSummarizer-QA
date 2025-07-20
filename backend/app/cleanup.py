"""
Utility functions for cleaning up downloaded files and resources.
"""
import os
import glob
import shutil
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def cleanup_video_files(video_id: str) -> Dict[str, int]:
    """
    Clean up files related to a specific video ID.
    Returns counts of deleted files by type.
    """
    deleted_counts = {
        "audio": 0,
        "transcripts": 0,
        "vector_stores": 0,
    }
    
    # Delete audio files
    audio_patterns = [
        f"./downloads/{video_id}.mp3",
        f"./downloads/{video_id}.*.vtt"  # For subtitle files
    ]
    
    for pattern in audio_patterns:
        for audio_file in glob.glob(pattern):
            try:
                os.remove(audio_file)
                deleted_counts["audio"] += 1
                logger.info(f"Deleted audio file: {audio_file}")
            except Exception as e:
                logger.error(f"Failed to delete audio file {audio_file}: {str(e)}")
    
    # Delete transcript file
    transcript_path = f"./downloads/transcripts/{video_id}.txt"
    if os.path.exists(transcript_path):
        try:
            os.remove(transcript_path)
            deleted_counts["transcripts"] += 1
            logger.info(f"Deleted transcript: {transcript_path}")
        except Exception as e:
            logger.error(f"Failed to delete transcript {transcript_path}: {str(e)}")
    
    # Delete vector store
    vector_store_path = os.path.join("./downloads/vector_stores", f"video_{video_id}")
    if os.path.exists(vector_store_path):
        try:
            shutil.rmtree(vector_store_path)
            deleted_counts["vector_stores"] += 1
            logger.info(f"Deleted vector store: {vector_store_path}")
        except Exception as e:
            logger.error(f"Failed to delete vector store {vector_store_path}: {str(e)}")
    
    return deleted_counts

def cleanup_all_files() -> Dict[str, int]:
    """
    Clean up all downloaded files for all videos.
    Returns counts of deleted files by type.
    """
    deleted_counts = {
        "audio": 0,
        "transcripts": 0,
        "vector_stores": 0,
    }
    
    # Delete all audio files in downloads
    try:
        audio_files = glob.glob("./downloads/*.mp3") + glob.glob("./downloads/*.vtt")
        for file in audio_files:
            try:
                os.remove(file)
                deleted_counts["audio"] += 1
            except Exception as e:
                logger.error(f"Failed to delete audio file {file}: {str(e)}")
    except Exception as e:
        logger.error(f"Error while cleaning up audio files: {str(e)}")
    
    # Delete all transcript files
    try:
        if os.path.exists("./downloads/transcripts"):
            transcript_files = glob.glob("./downloads/transcripts/*.txt")
            for file in transcript_files:
                try:
                    os.remove(file)
                    deleted_counts["transcripts"] += 1
                except Exception as e:
                    logger.error(f"Failed to delete transcript {file}: {str(e)}")
    except Exception as e:
        logger.error(f"Error while cleaning up transcript files: {str(e)}")
    
    # Delete all vector stores
    try:
        if os.path.exists("./downloads/vector_stores"):
            vector_store_dirs = [d for d in os.listdir("./downloads/vector_stores") 
                              if os.path.isdir(os.path.join("./downloads/vector_stores", d))]
            for dir_name in vector_store_dirs:
                try:
                    shutil.rmtree(os.path.join("./downloads/vector_stores", dir_name))
                    deleted_counts["vector_stores"] += 1
                except Exception as e:
                    logger.error(f"Failed to delete vector store {dir_name}: {str(e)}")
    except Exception as e:
        logger.error(f"Error while cleaning up vector stores: {str(e)}")
    
    return deleted_counts

def recreate_directories():
    """Recreate necessary directories after cleanup."""
    dirs = [
        "./downloads", 
        "./downloads/transcripts", 
        "./downloads/vector_stores", 
        "./downloads/logs"
    ]
    
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"Recreated directory: {dir_path}")
