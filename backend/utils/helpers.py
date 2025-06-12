"""
Utility functions for business scraper
"""

import re
import logging
from urllib.parse import urlparse, urljoin
from typing import Optional

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common unwanted characters
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    return text

def extract_phone_number(text: str) -> Optional[str]:
    """Extract phone number from text"""
    if not text:
        return None
    
    # Common phone number patterns
    patterns = [
        r'\+?\d{1,4}[\s\-\(\)]?\d{1,4}[\s\-\(\)]?\d{1,4}[\s\-\(\)]?\d{1,9}',
        r'\(\d{3}\)\s?\d{3}[\-\.]?\d{4}',
        r'\d{3}[\-\.]?\d{3}[\-\.]?\d{4}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0)
            # Clean up phone number
            phone = re.sub(r'[^\d\+]', '', phone)
            if len(phone) >= 7:  # Minimum valid phone length
                return phone
    
    return None

def extract_website_url(text: str) -> Optional[str]:
    """Extract website URL from text"""
    if not text:
        return None
    
    # URL patterns
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    match = re.search(url_pattern, text, re.IGNORECASE)
    
    if match:
        return match.group(0)
    
    # Domain pattern without protocol
    domain_pattern = r'www\.[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}'
    match = re.search(domain_pattern, text, re.IGNORECASE)
    
    if match:
        return f"http://{match.group(0)}"
    
    return None

def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def normalize_domain(domain: str) -> str:
    """Normalize domain URL"""
    if not domain.startswith(('http://', 'https://')):
        domain = f"https://{domain}"
    
    parsed = urlparse(domain)
    return f"{parsed.scheme}://{parsed.netloc}"

def extract_business_id_from_url(url: str) -> Optional[str]:
    """Extract business ID from Yello URL"""
    # Pattern: /company/{id}/{slug}
    match = re.search(r'/company/(\d+)/', url)
    return match.group(1) if match else None

def safe_int(value: str, default: int = 0) -> int:
    """Safely convert string to int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value: str, default: float = 0.0) -> float:
    """Safely convert string to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
