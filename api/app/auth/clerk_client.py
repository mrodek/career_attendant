from clerk_backend_api import Clerk
from typing import Optional, Dict
import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from ..config import Settings
from ..logger import logger

settings = Settings()

class ClerkClient:
    def __init__(self):
        if not settings.clerk_secret_key:
            logger.warning("CLERK_SECRET_KEY not configured")
            self.client = None
        else:
            self.client = Clerk(bearer_auth=settings.clerk_secret_key)
        
    async def verify_session(self, session_token: str) -> Optional[Dict]:
        """Verify a Clerk session token"""
        if not self.client:
            logger.error("Clerk client not initialized")
            return None
            
        try:
            response = await self.client.sessions.verify(
                session_id=session_token
            )
            return response.to_dict() if hasattr(response, 'to_dict') else dict(response)
        except Exception as e:
            logger.error(f"Session verification failed: {e}")
            return None
    
    async def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user details from Clerk"""
        if not self.client:
            logger.error("Clerk client not initialized")
            return None
            
        try:
            user = await self.client.users.get(user_id=user_id)
            return user.to_dict() if hasattr(user, 'to_dict') else dict(user)
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
    
    async def sync_user_to_db(self, clerk_user: Dict, db_session: Session):
        """Sync Clerk user to local database"""
        from ..models import User
        
        user = db_session.query(User).filter_by(
            id=clerk_user['id']
        ).first()
        
        # Extract email from Clerk user data
        email = None
        if 'email_addresses' in clerk_user and clerk_user['email_addresses']:
            email = clerk_user['email_addresses'][0].get('email_address')
        
        if not email:
            logger.error(f"No email found for user {clerk_user['id']}")
            return None
        
        if not user:
            # Create new user
            user = User(
                id=clerk_user['id'],
                email=email,
                username=clerk_user.get('username'),
                full_name=f"{clerk_user.get('first_name', '')} {clerk_user.get('last_name', '')}".strip()
            )
            db_session.add(user)
            logger.info(f"Created new user: {user.id}")
        else:
            # Update existing user
            user.email = email
            user.username = clerk_user.get('username')
            user.full_name = f"{clerk_user.get('first_name', '')} {clerk_user.get('last_name', '')}".strip()
            user.updated_at = datetime.utcnow()
            logger.info(f"Updated user: {user.id}")
        
        db_session.commit()
        db_session.refresh(user)
        return user

clerk_client = ClerkClient()
