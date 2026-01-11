from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import secrets
import hashlib
from ..auth.clerk_client import clerk_client
from ..auth.dependencies import get_current_user_id, get_current_user
from ..db import get_db
from ..models import User, UserSession
from ..logger import logger

router = APIRouter(prefix="/api/auth", tags=["authentication"])

class SessionValidationRequest(BaseModel):
    session_token: str

class SessionValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    expires_at: Optional[str] = None

class CreateSessionRequest(BaseModel):
    clerk_jwt: str

class CreateSessionResponse(BaseModel):
    session_token: str
    user_id: str
    expires_at: str

@router.post("/webhook/clerk")
async def clerk_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Clerk webhook events (user created, updated, deleted)
    Configure this endpoint in your Clerk Dashboard under Webhooks
    """
    try:
        payload = await request.json()
        event_type = payload.get('type')
        
        logger.info(f"Received Clerk webhook: {event_type}")
        
        if event_type == 'user.created' or event_type == 'user.updated':
            clerk_user = payload.get('data')
            if clerk_user:
                await clerk_client.sync_user_to_db(clerk_user, db)
                return {"status": "success", "event": event_type}
        
        elif event_type == 'user.deleted':
            user_id = payload.get('data', {}).get('id')
            if user_id:
                user = db.query(User).filter_by(id=user_id).first()
                if user:
                    db.delete(user)
                    db.commit()
                    logger.info(f"Deleted user: {user_id}")
                return {"status": "success", "event": event_type}
        
        return {"status": "ignored", "event": event_type}
    
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )

@router.get("/me")
async def get_current_user_info(
    user: User = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "subscription_tier": user.subscription_tier,
        "subscription_status": user.subscription_status,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    }

@router.post("/validate-session", response_model=SessionValidationResponse)
async def validate_session(
    request: SessionValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate a Clerk session token (used by Chrome extension)
    Returns session validity and user information
    """
    session = await clerk_client.verify_session(request.session_token)
    
    if not session:
        return SessionValidationResponse(valid=False)
    
    user_id = session.get('user_id')
    
    # Ensure user exists in our database
    if user_id:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            # Fetch from Clerk and sync
            clerk_user = await clerk_client.get_user(user_id)
            if clerk_user:
                await clerk_client.sync_user_to_db(clerk_user, db)
    
    return SessionValidationResponse(
        valid=True,
        user_id=user_id,
        expires_at=session.get('expire_at')
    )

@router.post("/sync-user")
async def sync_user_from_clerk(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Manually sync user data from Clerk to local database
    Useful for updating user information
    """
    clerk_user = await clerk_client.get_user(user_id)
    
    if not clerk_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in Clerk"
        )
    
    user = await clerk_client.sync_user_to_db(clerk_user, db)
    
    return {
        "status": "success",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name
        }
    }

@router.post("/create-session", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Exchange a Clerk JWT for a long-lived session token.
    This is the proper way to authenticate browser extensions.
    
    Flow:
    1. Extension gets Clerk JWT from auth page (one-time)
    2. Calls this endpoint to exchange JWT for session token
    3. Session token is valid for 7 days
    4. Extension uses session token for all subsequent requests
    """
    try:
        # Validate the Clerk JWT using the middleware's JWT validation
        from jose import jwt
        from ..auth.middleware import get_jwks_keys
        
        # Get unverified header to find the key ID
        unverified_header = jwt.get_unverified_header(request.clerk_jwt)
        kid = unverified_header.get('kid')
        
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT: missing key ID"
            )
        
        # Fetch JWKS keys
        jwks = await get_jwks_keys()
        if not jwks:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to fetch JWKS keys"
            )
        
        # Find the matching key
        key = next((jwk for jwk in jwks.get('keys', []) if jwk.get('kid') == kid), None)
        
        if not key:
            # Try refreshing the cache
            jwks = await get_jwks_keys(force_refresh=True)
            if jwks:
                key = next((jwk for jwk in jwks.get('keys', []) if jwk.get('kid') == kid), None)
        
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find matching key for JWT validation"
            )
        
        # Decode and verify JWT
        payload = jwt.decode(
            request.clerk_jwt,
            key,
            algorithms=['RS256'],
            options={"verify_aud": False}
        )
        
        user_id = payload.get('sub')
        user_email = payload.get('email')
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT: missing user ID"
            )
        
        # Ensure user exists in database
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            # Try to fetch from Clerk and sync
            clerk_user = await clerk_client.get_user(user_id)
            if clerk_user:
                user = await clerk_client.sync_user_to_db(clerk_user, db)
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        
        # Generate a secure session token
        session_token = secrets.token_urlsafe(32)
        
        # Hash the token before storing (security best practice)
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()
        
        # Set expiration to 7 days from now
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Create session in database
        db_session = UserSession(
            user_id=user_id,
            session_token=token_hash,
            ip_address=http_request.client.host if http_request else None,
            user_agent=http_request.headers.get('User-Agent') if http_request else None,
            expires_at=expires_at
        )
        db.add(db_session)
        db.commit()
        
        logger.info(f"Created session for user {user_id}, expires at {expires_at}")
        
        return CreateSessionResponse(
            session_token=session_token,  # Return unhashed token to client
            user_id=user_id,
            expires_at=expires_at.isoformat()
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT has expired"
        )
    except jwt.JWTError as e:
        logger.error(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid JWT: {str(e)}"
        )
    except Exception as e:
        import traceback
        logger.error(f"Session creation failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )
