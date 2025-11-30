from sqlalchemy.orm import Session
from . import models
from .models import User, SavedJob
from .schemas import EntryIn
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.2, max=2))
def upsert_user_by_email(db: Session, email: Optional[str], user_id: Optional[str] = None) -> Optional[User]:
    """
    Find or create a user by email.
    If user_id is provided (Chrome ID or Clerk ID), use it for new users.
    """
    if not email:
        return None
    
    # Try to find existing user by email
    user = db.query(User).filter(User.email == email).one_or_none()
    if user:
        return user
    
    # If user_id provided, check if user exists with that ID
    if user_id:
        existing = db.query(User).filter(User.id == user_id).one_or_none()
        if existing:
            return existing
    
    # Create new user with provided ID or generate one
    if not user_id:
        import uuid
        user_id = str(uuid.uuid4())  # Fallback to UUID if no ID provided
    
    user = User(id=user_id, email=email)
    db.add(user)
    db.flush()  # Flush to get the ID, but don't commit yet
    return user

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.2, max=2))
def create_entry(db: Session, user: Optional[User], payload: EntryIn) -> SavedJob:
    entry = SavedJob(
        user_id=user.id if user else None,
        job_url=payload.jobUrl,
        job_title=payload.jobTitle,
        company_name=payload.companyName,
        job_description=payload.jobDescription,
        salary_range=payload.salaryRange,
        location=payload.location,
        remote_type=payload.remoteType,
        role_type=payload.roleType,
        interest_level=payload.interestLevel,
        application_status=payload.applicationStatus,
        application_date=payload.applicationDate,
        notes=payload.notes,
        source=payload.source,
        scraped_data=payload.scrapedData,
    )
    db.add(entry)
    db.flush()  # Flush to get the ID, but don't commit yet
    return entry
