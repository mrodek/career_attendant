from fastapi import Request, status
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from jose.backends import RSAKey
import httpx
import hashlib
from ..config import Settings
from ..logger import logger
import json
from datetime import datetime, timedelta

def auth_error_response(status_code: int, detail: str) -> JSONResponse:
    """Return a JSON error response for middleware (can't use HTTPException)"""
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

settings = Settings()

# Cache for JWKS keys with TTL
_jwks_cache = None
_jwks_cache_expires_at = None
JWKS_CACHE_TTL_HOURS = 1  # Refresh cache every hour

async def get_jwks_keys(force_refresh: bool = False):
    """Fetch JWKS keys from Clerk with TTL-based caching"""
    global _jwks_cache, _jwks_cache_expires_at
    
    now = datetime.utcnow()
    
    # Return cached keys if still valid and not forcing refresh
    if not force_refresh and _jwks_cache is not None and _jwks_cache_expires_at:
        if now < _jwks_cache_expires_at:
            logger.debug("Using cached JWKS keys")
            return _jwks_cache
    
    if not settings.clerk_jwks_url:
        return None
    
    try:
        logger.info("Fetching fresh JWKS keys from Clerk")
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.clerk_jwks_url)
            response.raise_for_status()
            jwks = response.json()
            _jwks_cache = jwks
            _jwks_cache_expires_at = now + timedelta(hours=JWKS_CACHE_TTL_HOURS)
            return jwks
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        # Return stale cache if available when fetch fails
        if _jwks_cache is not None:
            logger.warning("Using stale JWKS cache due to fetch failure")
            return _jwks_cache
        return None

class AuthMiddleware:
    """Middleware to verify JWT tokens from Clerk"""
    
    async def __call__(self, request: Request, call_next):
        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Skip auth for public endpoints
        public_paths = ['/docs', '/openapi.json', '/health', '/api/auth/webhook', '/api/auth/create-session', '/auth/login', '/auth/callback', '/extract', '/favicon.ico']
        
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
        
        # Extract token from header (JWT authentication priority)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                # Validate JWT token
                payload = await validate_jwt_token(token)
                request.state.user_id = payload.sub
                request.state.session_id = payload.sid
                request.state.user_email = payload.email
                logger.debug(f"JWT authentication successful for user: {payload.sub}")
                return await call_next(request)
            except Exception as e:
                logger.warning(f"JWT validation failed: {e}")
                # Continue to API key fallback
        
        # Check for API key authentication (fallback)
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

async def AuthenticationMiddleware(request: Request, call_next):
    """Main authentication middleware"""
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
    
    # Extract token from header (JWT authentication priority)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            # Validate JWT token
            payload = await validate_jwt_token(token)
            request.state.user_id = payload.sub
            request.state.session_id = payload.sid
            request.state.user_email = payload.email
            logger.debug(f"JWT authentication successful for user: {payload.sub}")
            return await call_next(request)
        except Exception as e:
            logger.warning(f"JWT validation failed: {e}")
            # Continue to API key fallback
    
    # Check for API key authentication (fallback)
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

                if not key:
                    logger.error(f"Unable to find matching key for kid: {kid}")
                    return auth_error_response(
                        status.HTTP_401_UNAUTHORIZED,
                        "Unable to find a matching public key to verify the token."
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
                
                logger.info(f"✓ JWT auth successful for {request.url.path} - User: {request.state.user_id}")
                
            except jwt.ExpiredSignatureError as e:
                logger.warning(f"JWT expired for {request.url.path}: {str(e)}")
                return auth_error_response(
                    status.HTTP_401_UNAUTHORIZED,
                    "Token has expired"
                )
            except JWTError as e:
                logger.error(f"JWT validation failed for {request.url.path}: {str(e)}")
                return auth_error_response(
                    status.HTTP_401_UNAUTHORIZED,
                    f"Invalid token: {str(e)}"
                )
        else:
            # Validate as session token
            from ..db import get_db
            from ..models import UserSession
            
            # Get database session
            db = next(get_db())
            
            try:
                # Hash the token to compare with stored hash
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                
                # Look up session in database
                session = db.query(UserSession).filter(
                    UserSession.session_token == token_hash,
                    UserSession.expires_at > datetime.utcnow()
                ).first()
                
                if not session:
                    logger.warning(f"Session token invalid or expired for {request.url.path}")
                    return auth_error_response(
                        status.HTTP_401_UNAUTHORIZED,
                        "Invalid or expired session token"
                    )
                
                # Add user context to request state
                request.state.user_id = session.user_id
                request.state.session_id = str(session.id)
                
                # Get user email from user table
                from ..models import User
                user = db.query(User).filter(User.id == session.user_id).first()
                request.state.user_email = user.email if user else None
                
                logger.info(f"✓ Session auth successful for {request.url.path} - User: {request.state.user_id}")
                
            finally:
                db.close()
        
        response = await call_next(request)
        return response
