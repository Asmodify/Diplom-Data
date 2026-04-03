"""
Utility Helpers v2.0
====================
Common utility functions.
"""

import logging
import re
import time
from datetime import datetime
from functools import wraps
from typing import Optional, Callable, Any
from pathlib import Path


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level
        log_file: Optional log file path
        format_string: Custom format string
        
    Returns:
        Root logger
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
    handlers = [logging.StreamHandler()]
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
        
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=handlers,
        force=True,
    )
    
    return logging.getLogger()


def sanitize_text(text: Optional[str]) -> str:
    """
    Sanitize text for storage.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
        
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Strip
    text = text.strip()
    
    return text


def extract_numbers(text: str) -> list[int]:
    """
    Extract numbers from text.
    
    Args:
        text: Text containing numbers
        
    Returns:
        List of extracted integers
    """
    if not text:
        return []
        
    # Handle K, M suffixes
    text = text.upper()
    text = re.sub(r'(\d+\.?\d*)K', lambda m: str(int(float(m.group(1)) * 1000)), text)
    text = re.sub(r'(\d+\.?\d*)M', lambda m: str(int(float(m.group(1)) * 1000000)), text)
    
    # Find all numbers
    numbers = re.findall(r'\d+', text)
    return [int(n) for n in numbers]


def parse_count(text: str) -> int:
    """
    Parse count from text like "1.2K likes".
    
    Args:
        text: Text with count
        
    Returns:
        Integer count
    """
    if not text:
        return 0
        
    text = text.upper().strip()
    
    # Handle K/M suffixes
    match = re.search(r'(\d+\.?\d*)\s*([KM])?', text)
    if match:
        num = float(match.group(1))
        suffix = match.group(2)
        if suffix == 'K':
            return int(num * 1000)
        elif suffix == 'M':
            return int(num * 1000000)
        return int(num)
    return 0


def format_timestamp(dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime object (default: now)
        fmt: Format string
        
    Returns:
        Formatted string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


def parse_timestamp(text: str) -> Optional[datetime]:
    """
    Parse timestamp from Facebook-style text.
    
    Args:
        text: Timestamp text like "2h", "1d", "March 15"
        
    Returns:
        Datetime or None
    """
    if not text:
        return None
        
    text = text.lower().strip()
    now = datetime.now()
    
    # Relative times
    if 'just now' in text or 'now' in text:
        return now
    elif 'min' in text or 'm' in text:
        match = re.search(r'(\d+)', text)
        if match:
            from datetime import timedelta
            return now - timedelta(minutes=int(match.group(1)))
    elif 'hour' in text or 'h' in text:
        match = re.search(r'(\d+)', text)
        if match:
            from datetime import timedelta
            return now - timedelta(hours=int(match.group(1)))
    elif 'day' in text or 'd' in text:
        match = re.search(r'(\d+)', text)
        if match:
            from datetime import timedelta
            return now - timedelta(days=int(match.group(1)))
    elif 'week' in text or 'w' in text:
        match = re.search(r'(\d+)', text)
        if match:
            from datetime import timedelta
            return now - timedelta(weeks=int(match.group(1)))
            
    return None


def retry_with_backoff(
    func: Optional[Callable] = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for retry with exponential backoff.
    
    Args:
        func: Function to wrap
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay
        exceptions: Exceptions to catch
        
    Usage:
        @retry_with_backoff(max_retries=3)
        def my_function():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = base_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay)
                        delay = min(delay * 2, max_delay)
                    else:
                        raise
                        
            raise last_exception
        return wrapper
        
    if func is not None:
        return decorator(func)
    return decorator


def create_safe_filename(text: str, max_length: int = 100) -> str:
    """
    Create safe filename from text.
    
    Args:
        text: Source text
        max_length: Maximum length
        
    Returns:
        Safe filename
    """
    if not text:
        return "unnamed"
        
    # Replace unsafe characters
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', text)
    safe = re.sub(r'\s+', '_', safe)
    safe = re.sub(r'_+', '_', safe)
    safe = safe.strip('_')
    
    # Truncate
    if len(safe) > max_length:
        safe = safe[:max_length]
        
    return safe or "unnamed"


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Split list into chunks.
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def deep_merge(base: dict, update: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        update: Dictionary with updates
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
            
    return result


class RateLimiter:
    """Simple rate limiter."""
    
    def __init__(self, calls_per_second: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_second: Maximum calls per second
        """
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0
        
    def wait(self):
        """Wait if needed before next call."""
        now = time.time()
        elapsed = now - self.last_call
        
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
            
        self.last_call = time.time()
        
    def __call__(self, func):
        """Use as decorator."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.wait()
            return func(*args, **kwargs)
        return wrapper
