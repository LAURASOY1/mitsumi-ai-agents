from typing import Optional, List, Dict, Any, Union, Callable, TypeVar, Tuple
from typing import Optional, List, Dict, Any, Union
from typing import Optional, List, Dict, Any
import hashlib
import secrets
import base64
from typing import Optional

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash a password with a salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Use PBKDF2 for secure password hashing
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    
    # Combine salt and hash
    return f"{salt}:{base64.b64encode(hash_obj).decode('utf-8')}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash"""
    try:
        salt, hash_str = hashed.split(':')
        return hash_password(password, salt) == hashed
    except ValueError:
        return False

def normalize_email(email: str) -> str:
    """Normalize email to lowercase"""
    return email.strip().lower()

def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)
