import logging
import os
import sys
from datetime import datetime

def setup_logger(name, log_level=logging.INFO):
    """Configure and return a logger instance."""
    # Create logs directory under downloads folder if it doesn't exist
    logs_dir = os.path.join('./downloads/logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Avoid adding handlers if they already exist
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        
        # File handler
        log_filename = f"{logs_dir}/{datetime.now().strftime('%Y%m%d')}_yt_rag.log"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(log_level)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        
        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger