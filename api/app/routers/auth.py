from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..auth.clerk_client import clerk_client
from ..auth.dependencies import get_current_user_id, get_current_user
from ..db import get_db
from ..models import User
from ..logger import logger

router = APIRouter(prefix="/api/auth", tags=["authentication"])

class SessionValidationRequest(BaseModel):
    session_token: str

class SessionValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    expires_at: Optional[str] = None

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
