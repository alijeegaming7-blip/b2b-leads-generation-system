"""
Data validation module with comprehensive email, phone, URL and password validation.
"""
import re
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def validate_email(email: Optional[str]) -> bool:
    """Validate email address format."""
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip().lower()
    if len(email) > 320:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: Optional[str]) -> bool:
    """Validate phone number - accepts international formats."""
    if not phone or not isinstance(phone, str):
        return False
    
    digits = re.sub(r'[^\d]', '', phone)
    return 7 <= len(digits) <= 15


def validate_url(url: Optional[str]) -> bool:
    """Validate URL format and protocol."""
    if not url or not isinstance(url, str):
        return False
    
    try:
        parsed = urlparse(url.strip())
        return bool(parsed.scheme and parsed.netloc and parsed.scheme in ['http', 'https'])
    except Exception:
        return False


def sanitize_business_name(name: Optional[str], max_length: int = 200) -> str:
    """Sanitize business name."""
    if not name or not isinstance(name, str):
        return ""
    
    name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:max_length] if len(name) > max_length else name


def sanitize_text_input(text: Optional[str], max_length: int = 5000) -> str:
    """Sanitize general text input."""
    if not text or not isinstance(text, str):
        return ""
    
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_length] if len(text) > max_length else text


def validate_password_strength(password: Optional[str]) -> Tuple[bool, str]:
    """Validate password meets security requirements."""
    if not password:
        return (False, "Password is required")
    
    if len(password) < 8:
        return (False, "Password must be at least 8 characters long")
    
    if len(password) > 128:
        return (False, "Password too long")
    
    if not re.search(r'[A-Z]', password):
        return (False, "Password must contain an uppercase letter")
    
    if not re.search(r'[a-z]', password):
        return (False, "Password must contain a lowercase letter")
    
    if not re.search(r'\d', password):
        return (False, "Password must contain a digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
        return (False, "Password must contain a special character")
    
    return (True, "")
