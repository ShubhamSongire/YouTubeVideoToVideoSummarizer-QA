#!/usr/bin/env python
# Migration script to move vector store files and logs to the downloads folder
import os
import shutil
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def ensure_dir(dir_path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        logger.info(f"Created directory: {dir_path}")

def migrate_vector_stores():
    """Migrate vector store files to downloads/vector_stores folder."""
    # Create target directory
    target_dir = "./downloads/vector_stores"
    ensure_dir(target_dir)
    
    # Find all video_* folders in root directory
    root_dir = "."
    migrated = 0
    
    for item in os.listdir(root_dir):
        if item.startswith("video_") and os.path.isdir(os.path.join(root_dir, item)):
            source_dir = os.path.join(root_dir, item)
            dest_dir = os.path.join(target_dir, item)
            
            # Check if this is a vector store folder (has index.faiss and index.pkl)
            if (os.path.exists(os.path.join(source_dir, "index.faiss")) and 
                os.path.exists(os.path.join(source_dir, "index.pkl"))):
                
                # Skip if already migrated
                if os.path.exists(dest_dir):
                    logger.info(f"Vector store {item} already exists in downloads folder, skipping.")
                    continue
                
                # Copy directory and contents
                ensure_dir(dest_dir)
                shutil.copy2(
                    os.path.join(source_dir, "index.faiss"),
                    os.path.join(dest_dir, "index.faiss")
                )
                shutil.copy2(
                    os.path.join(source_dir, "index.pkl"),
                    os.path.join(dest_dir, "index.pkl")
                )
                logger.info(f"Migrated vector store: {item}")
                migrated += 1
    
    # Also check backend/vector_stores directory
    backend_vector_stores = "./backend/vector_stores"
    if os.path.exists(backend_vector_stores):
        for item in os.listdir(backend_vector_stores):
            if os.path.isdir(os.path.join(backend_vector_stores, item)):
                source_dir = os.path.join(backend_vector_stores, item)
                dest_dir = os.path.join(target_dir, item)
                
                # Check if this is a vector store folder
                if (os.path.exists(os.path.join(source_dir, "index.faiss")) and 
                    os.path.exists(os.path.join(source_dir, "index.pkl"))):
                    
                    # Skip if already migrated
                    if os.path.exists(dest_dir):
                        logger.info(f"Vector store {item} already exists in downloads folder, skipping.")
                        continue
                    
                    # Copy directory and contents
                    ensure_dir(dest_dir)
                    shutil.copy2(
                        os.path.join(source_dir, "index.faiss"),
                        os.path.join(dest_dir, "index.faiss")
                    )
                    shutil.copy2(
                        os.path.join(source_dir, "index.pkl"),
                        os.path.join(dest_dir, "index.pkl")
                    )
                    logger.info(f"Migrated vector store from backend: {item}")
                    migrated += 1
    
    logger.info(f"Total vector stores migrated: {migrated}")

def migrate_logs():
    """Migrate log files to downloads/logs folder."""
    # Create target directory
    target_dir = "./downloads/logs"
    ensure_dir(target_dir)
    
    # Migrate logs from the logs directory
    logs_dir = "./logs"
    migrated = 0
    
    if os.path.exists(logs_dir):
        for item in os.listdir(logs_dir):
            if item.endswith("_yt_rag.log"):
                source_file = os.path.join(logs_dir, item)
                dest_file = os.path.join(target_dir, item)
                
                # Skip if already migrated
                if os.path.exists(dest_file):
                    logger.info(f"Log file {item} already exists in downloads folder, skipping.")
                    continue
                
                shutil.copy2(source_file, dest_file)
                logger.info(f"Migrated log file: {item}")
                migrated += 1
    
    # Also check backend/logs directory
    backend_logs_dir = "./backend/logs"
    if os.path.exists(backend_logs_dir):
        for item in os.listdir(backend_logs_dir):
            if item.endswith("_yt_rag.log"):
                source_file = os.path.join(backend_logs_dir, item)
                dest_file = os.path.join(target_dir, item)
                
                # Skip if already migrated
                if os.path.exists(dest_file):
                    logger.info(f"Log file {item} already exists in downloads folder, skipping.")
                    continue
                
                shutil.copy2(source_file, dest_file)
                logger.info(f"Migrated log file from backend: {item}")
                migrated += 1
    
    logger.info(f"Total log files migrated: {migrated}")

def migrate_transcripts():
    """Migrate transcript files to downloads/transcripts folder."""
    # Create target directory
    target_dir = "./downloads/transcripts"
    ensure_dir(target_dir)
    
    # Migrate transcripts from the transcripts directory
    transcripts_dir = "./transcripts"
    migrated = 0
    
    if os.path.exists(transcripts_dir):
        for item in os.listdir(transcripts_dir):
            if item.endswith(".txt"):
                source_file = os.path.join(transcripts_dir, item)
                dest_file = os.path.join(target_dir, item)
                
                # Skip if already migrated
                if os.path.exists(dest_file):
                    logger.info(f"Transcript file {item} already exists in downloads folder, skipping.")
                    continue
                
                shutil.copy2(source_file, dest_file)
                logger.info(f"Migrated transcript file: {item}")
                migrated += 1
    
    # Also check backend/transcripts directory
    backend_transcripts_dir = "./backend/transcripts"
    if os.path.exists(backend_transcripts_dir):
        for item in os.listdir(backend_transcripts_dir):
            if item.endswith(".txt"):
                source_file = os.path.join(backend_transcripts_dir, item)
                dest_file = os.path.join(target_dir, item)
                
                # Skip if already migrated
                if os.path.exists(dest_file):
                    logger.info(f"Transcript file {item} already exists in downloads folder, skipping.")
                    continue
                
                shutil.copy2(source_file, dest_file)
                logger.info(f"Migrated transcript file from backend: {item}")
                migrated += 1
    
    logger.info(f"Total transcript files migrated: {migrated}")

def main():
    """Run the migration process."""
    logger.info("Starting migration to downloads folder structure...")
    
    # Ensure downloads directory exists
    ensure_dir("./downloads")
    
    # Migrate vector stores
    migrate_vector_stores()
    
    # Migrate logs
    migrate_logs()
    
    # Migrate transcripts
    migrate_transcripts()
    
    logger.info("Migration completed successfully!")

if __name__ == "__main__":
    main()
