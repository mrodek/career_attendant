from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional
from ..db import get_db
from ..models import User
from ..config import Settings

settings = Settings()

async def get_current_user_id(request: Request) -> str:
    """Dependency to get current user ID from request state"""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user_id

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user from database"""
    user_id = await get_current_user_id(request)
    
    user = db.query(User).filter_by(id=user_id).first()
    
    # Auto-create user if they don't exist (first-time sign-in via Clerk)
    if not user:
        # Get email from request state (set by middleware)
        user_email = getattr(request.state, 'user_email', None)
        
        if settings.dev_mode and user_id == "dev_user":
            # Dev mode user
            user = User(
                id="dev_user",
                email="dev@example.com",
                username="devuser",
                full_name="Dev User",
                subscription_tier="free"
            )
        elif user_id == "api_user":
            # API key authentication - create system user
            user = User(
                id="api_user",
                email="api@example.com",
                username="apiuser",
                full_name="API User",
                subscription_tier="free"
            )
        elif user_id.startswith("user_"):
            # Real Clerk user - auto-create on first sign-in
            user = User(
                id=user_id,
                email=user_email or f"{user_id}@clerk.user",
                username=user_id,
                subscription_tier="free"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user

def require_subscription_tier(required_tier: str):
    """Dependency factory to check user's subscription tier"""
    
    async def tier_checker(
        user: User = Depends(get_current_user)
    ) -> User:
        tier_levels = {"free": 0, "basic": 1, "pro": 2}
        user_level = tier_levels.get(user.subscription_tier, 0)
        required_level = tier_levels.get(required_tier, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {required_tier} subscription"
            )
        
        return user
    
    return tier_checker

async def check_feature_access(
    feature_name: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """Check if user has access to a specific feature"""
    from ..models import FeatureAccess
    
    feature = db.query(FeatureAccess).filter_by(
        user_id=user.id,
        feature_name=feature_name
    ).first()
    
    if not feature:
        # No record means no explicit restriction
        return True
    
    if not feature.access_granted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access to {feature_name} is not available on your plan"
        )
    
    # Check usage limits
    if feature.usage_limit and feature.usage_count >= feature.usage_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Usage limit reached for {feature_name}"
        )
    
    return True
