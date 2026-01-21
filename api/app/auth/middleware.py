"""
Authentication middleware for Career Attendant API
Handles API key authentication (JWT temporarily disabled)
"""

import logging
from typing import Optional

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from ..config import settings

logger = logging.getLogger(__name__)

def auth_error_response(status_code: int, detail: str) -> JSONResponse:
    """Return a standardized error response"""
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail}
    )

def is_public_path(path: str) -> bool:
    """Check if path is public (doesn't require authentication)"""
    public_paths = {
        "/health",
        "/",
        "/docs",
        "/openapi.json",
        "/favicon.ico",
        "/static",
    }
    
    # Check exact matches
    if path in public_paths:
        return True
    
    # Check path prefixes
    for public_path in public_paths:
        if path.startswith(public_path):
            return True
    
    return False

class AuthMiddleware:
    """Main authentication middleware - API key authentication"""
    
    async def __call__(self, request: Request, call_next):
        # Public paths that don't require authentication
        if is_public_path(request.url.path):
            return await call_next(request)
        
        # Development mode: bypass authentication if explicitly enabled
        if settings.dev_mode:
            logger.warning("⚠️  DEV_MODE enabled - bypassing authentication (NEVER use in production!)")
            request.state.user_id = "dev_user"
            request.state.session_id = "dev_session"
            request.state.user_email = "dev@example.com"
            return await call_next(request)
        
        # Check for API key authentication
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == settings.api_key:
            logger.debug("API key authentication successful")
            request.state.user_id = "api_user"
            request.state.session_id = "api_session"
            request.state.user_email = "api@example.com"
            return await call_next(request)
        
        # No valid authentication found
        logger.warning(f"Auth failed for {request.url.path}: Missing or invalid authorization header")
        return auth_error_response(
            status.HTTP_401_UNAUTHORIZED,
            "Missing or invalid authorization header"
        )
