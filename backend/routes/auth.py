"""
Authentication routes for admin login.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from backend.auth import (
    LoginRequest,
    TokenResponse,
    verify_admin_credentials,
    create_access_token,
    require_auth
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Admin login endpoint.
    
    Validates credentials against ADMIN_EMAIL and ADMIN_PASSWORD from .env
    Returns JWT token for authenticated access.
    
    Example:
        POST /api/v1/auth/login
        {
            "email": "admin@example.com",
            "password": "your-password"
        }
    """
    logger.info(f"Login attempt for email: {request.email}")
    
    if not verify_admin_credentials(request.email, request.password):
        logger.warning(f"Failed login attempt for: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(request.email)
    logger.info(f"Successful login for: {request.email}")
    
    return TokenResponse(access_token=access_token)


@router.get("/verify")
async def verify(payload: dict = Depends(require_auth)):
    """
    Verify if token is valid.
    
    Requires authentication header:
        Authorization: Bearer <token>
    
    Returns user info if token is valid.
    """
    return {
        "valid": True,
        "email": payload.get("email"),
        "role": payload.get("role"),
        "exp": payload.get("exp")
    }


@router.post("/logout")
async def logout(payload: dict = Depends(require_auth)):
    """
    Logout endpoint (stateless - just invalidates client-side token).
    
    In a stateless JWT system, logout is handled client-side by
    removing the token. This endpoint exists for API completeness.
    """
    logger.info(f"Logout for: {payload.get('email')}")
    return {"message": "Logged out successfully"}
