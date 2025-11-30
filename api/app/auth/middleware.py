from fastapi import Request, HTTPException, status
from jose import jwt, JWTError
from jose.backends import RSAKey
import httpx
from ..config import Settings
from ..logger import logger
import json

settings = Settings()

# Cache for JWKS keys
_jwks_cache = None

async def get_jwks_keys():
    """Fetch JWKS keys from Clerk"""
    global _jwks_cache
    
    if _jwks_cache is not None:
        return _jwks_cache
    
    if not settings.clerk_jwks_url:
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.clerk_jwks_url)
            response.raise_for_status()
            jwks = response.json()
            _jwks_cache = jwks
            return jwks
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        return None

class AuthMiddleware:
    """Middleware to verify JWT tokens from Clerk"""
    
    async def __call__(self, request: Request, call_next):
        # Skip auth for public endpoints
        public_paths = ['/docs', '/openapi.json', '/health', '/api/auth/webhook', '/auth/login', '/auth/callback']
        
        # Check if path starts with any public path
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        # Development mode: bypass authentication if explicitly enabled
        if settings.dev_mode:
            logger.warning("⚠️  DEV_MODE enabled - bypassing authentication (NEVER use in production!)")
            request.state.user_id = "dev_user"
            request.state.session_id = "dev_session"
            request.state.user_email = "dev@example.com"
            return await call_next(request)
        
        # Extract token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header.split(' ')[1]
        
        try:
            # Get unverified header to find the key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing key ID"
                )
            
            # Fetch JWKS keys
            jwks = await get_jwks_keys()
            if not jwks:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unable to fetch JWKS keys"
                )
            
            # Find the matching key
            key = None
            for jwk in jwks.get('keys', []):
                if jwk.get('kid') == kid:
                    key = jwk
                    break
            
            if not key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find matching key"
                )
            
            # Decode and verify JWT using the public key from JWKS
            payload = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                options={"verify_aud": False}
            )
            
            # Add user context to request state
            request.state.user_id = payload.get('sub')
            request.state.session_id = payload.get('sid')
            request.state.user_email = payload.get('email')
            
            logger.debug(f"Authenticated user: {request.state.user_id}")
            
        except JWTError as e:
            logger.error(f"JWT validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        
        response = await call_next(request)
        return response
