"""
Common utilities for Facebook Scraper
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Configure logging
def setup_logging(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging for a module
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional log file path
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # File handler if requested
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Path utilities
def get_project_root() -> Path:
    """Get absolute path to project root directory"""
    return Path(__file__).parent.parent

def ensure_dir(path: Path) -> Path:
    """
    Ensure directory exists, creating it if necessary
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    path.mkdir(parents=True, exist_ok=True)
    return path

def clean_filename(filename: str) -> str:
    """
    Clean a filename to be safe for all operating systems
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    # Replace unsafe characters
    unsafe = '<>:"/\\|?*'
    for char in unsafe:
        filename = filename.replace(char, '_')
    return filename.strip()

# Date utilities
def parse_fb_date(date_str: str) -> Optional[datetime]:
    """
    Parse a Facebook date string into datetime
    
    Args:
        date_str: Date string from Facebook
        
    Returns:
        Datetime object or None if parsing fails
    """
    try:
        from dateutil.parser import parse
        return parse(date_str)
    except:
        return None
