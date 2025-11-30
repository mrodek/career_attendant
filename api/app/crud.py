from sqlalchemy.orm import Session
from . import models
from .models import User, SavedJob
from .schemas import EntryIn
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.2, max=2))
def upsert_user_by_email(db: Session, email: Optional[str]) -> Optional[User]:
    if not email:
        return None
    user = db.query(User).filter(User.email == email).one_or_none()
    if user:
        return user
    user = User(email=email)
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
