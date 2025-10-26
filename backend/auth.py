"""
Authentication module for admin-only access.
Uses JWT tokens with credentials from environment variables.
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Load admin credentials from environment
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # Should be changed in .env
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Security scheme
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request model."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_HOURS * 3600  # seconds


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def verify_admin_credentials(email: str, password: str) -> bool:
    """
    Verify admin credentials against environment variables.
    
    Args:
        email: User email
        password: Plain text password
        
    Returns:
        True if credentials match, False otherwise
    """
    # Simple comparison for admin (no hashing needed for single admin)
    return email == ADMIN_EMAIL and password == ADMIN_PASSWORD


def create_access_token(email: str) -> str:
    """
    Create JWT access token.
    
    Args:
        email: User email
        
    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": email,
        "email": email,
        "role": "admin",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT token and return payload.
    
    Args:
        credentials: HTTP bearer credentials
        
    Returns:
        Token payload dict
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        email = payload.get("email")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing email",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Dependency for protected routes
async def require_auth(payload: dict = Depends(verify_token)) -> dict:
    """
    Dependency to require authentication on routes.
    
    Usage:
        @router.get("/protected", dependencies=[Depends(require_auth)])
        async def protected_route():
            ...
    """
    return payload


# Simplified dependency (just check authentication)
RequireAuth = Depends(require_auth)
