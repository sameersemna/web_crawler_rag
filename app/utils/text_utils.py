"""
Utility functions for text processing and validation
"""
import re
from typing import List
from urllib.parse import urlparse
import validators


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    return validators.url(url) is True


def normalize_url(url: str) -> str:
    """
    Normalize URL to standard format
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL
    """
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    return url


def extract_domain(url: str) -> str:
    """
    Extract domain from URL
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name
    """
    parsed = urlparse(url)
    return parsed.netloc


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and special characters
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def detect_language(text: str) -> str:
    """
    Detect language of text (simple heuristic)
    
    Args:
        text: Text to analyze
        
    Returns:
        Language code (en, ar, hi, ur, etc.)
    """
    # Simple heuristic based on character ranges
    if re.search(r'[\u0600-\u06FF]', text):
        return 'ar'  # Arabic
    elif re.search(r'[\u0900-\u097F]', text):
        return 'hi'  # Hindi
    elif re.search(r'[\u0600-\u06FF\u0750-\u077F]', text):
        return 'ur'  # Urdu
    else:
        return 'en'  # Default to English


def chunk_list(items: List, chunk_size: int) -> List[List]:
    """
    Split list into chunks
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255 - len(ext) - 1] + '.' + ext if ext else name[:255]
    
    return filename
