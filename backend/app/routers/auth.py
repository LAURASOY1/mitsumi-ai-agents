"""
Authentication routes - Fixed version
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
from datetime import datetime, timedelta
import hashlib
import base64
import json

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ============================================
# MODELS
# ============================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# ============================================
# CONFIGURATION
# ============================================

JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'development_secret_12345')
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ============================================
# USER STORE (Simple hash for passwords)
# ============================================

def hash_password(password: str) -> str:
    """Simple password hashing (SHA256)"""
    return hashlib.sha256(password.encode()).hexdigest()

USERS = {
    "admin@mitsumi.ai": {
        "id": "user_001",
        "email": "admin@mitsumi.ai",
        "password_hash": hash_password("admin123"),
        "name": "Admin User",
        "role": "admin"
    },
    "user@mitsumi.ai": {
        "id": "user_002",
        "email": "user@mitsumi.ai",
        "password_hash": hash_password("password123"),
        "name": "Test User",
        "role": "user"
    },
    "test@example.com": {
        "id": "user_003",
        "email": "test@example.com",
        "password_hash": hash_password("test123"),
        "name": "Test User",
        "role": "user"
    }
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def create_token(data: dict) -> str:
    """Create a simple token (no JWT library needed)"""
    token_data = {
        "sub": data.get("id"),
        "email": data.get("email"),
        "role": data.get("role", "user"),
        "exp": (datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()
    }
    # Simple encoding (for testing only)
    token_json = json.dumps(token_data)
    return base64.b64encode(token_json.encode()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain) == hashed

# ============================================
# ROUTES
# ============================================

@router.post("/login")
async def login(request: LoginRequest):
    """Authenticate user and return token"""
    print(f"🔐 Login attempt: {request.email}")
    
    # Find user
    user = USERS.get(request.email)
    if not user:
        print(f"❌ User not found: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        print(f"❌ Invalid password for: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create token
    token_data = {
        "id": user["id"],
        "email": user["email"],
        "role": user.get("role", "user")
    }
    access_token = create_token(token_data)
    
    print(f"✅ Login successful: {request.email}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name"),
            "role": user.get("role")
        }
    }

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify auth router is working"""
    return {
        "message": "Auth router is working!",
        "users": list(USERS.keys()),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/users")
async def list_users():
    """List all users (for testing only)"""
    return {
        "users": [
            {
                "email": user["email"],
                "name": user.get("name"),
                "role": user.get("role")
            }
            for user in USERS.values()
        ]
    }
