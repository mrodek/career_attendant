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
    
    # Check path prefixes (but not root "/" which would match everything)
    for public_path in public_paths:
        if public_path != "/" and path.startswith(public_path):
            return True
    
    return False

class AuthMiddleware:
    """Main authentication middleware - JWT first, API key fallback"""
    
    async def __call__(self, request: Request, call_next):
        # Allow OPTIONS requests for CORS preflight (they don't carry auth headers)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        logger.info(f"🔐 AuthMiddleware called for: {request.url.path}")
        
        # Public paths that don't require authentication
        if is_public_path(request.url.path):
            logger.info(f"✅ Public path, bypassing auth: {request.url.path}")
            return await call_next(request)
        
        # Development mode: bypass authentication if explicitly enabled
        if settings.dev_mode:
            logger.warning("⚠️  DEV_MODE enabled - bypassing authentication (NEVER use in production!)")
            request.state.user_id = "dev_user"
            request.state.session_id = "dev_session"
            request.state.user_email = "dev@example.com"
            return await call_next(request)
        
        # JWT authentication (priority)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                from ..jwt_utils import validate_jwt_token
                payload = await validate_jwt_token(token)
                request.state.user_id = payload.sub
                request.state.session_id = payload.sid
                request.state.user_email = payload.email
                logger.info(f"✅ JWT authentication successful for user: {payload.sub}")
                return await call_next(request)
            except Exception as e:
                logger.warning(f"JWT validation failed: {e}")
                # Continue to API key fallback
        
        # API key authentication (fallback - for development only)
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == settings.api_key:
            logger.warning("⚠️  Using API key auth - not secure for production!")
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
