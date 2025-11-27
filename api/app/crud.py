from sqlalchemy.orm import Session
from . import models
from .models import User, Entry, WorkType, SalaryRange, JobType
from .schemas import EntryIn
from typing import Optional, Tuple

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
    db.commit()
    db.refresh(user)
    return user

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.2, max=2))
def create_entry(db: Session, user: Optional[User], payload: EntryIn) -> Entry:
    entry = Entry(
        user_id=user.id if user else None,
        url=payload.url,
        title=payload.title,
        company=payload.company,
        work_type=WorkType(payload.workType) if payload.workType else None,
        salary_range=SalaryRange(payload.salaryRange) if payload.salaryRange else None,
        job_type=JobType(payload.jobType) if payload.jobType else None,
        location=payload.location,
        applied=payload.applied,
        user_email=payload.userEmail,
        user_identity_id=payload.userId,
        rating=payload.rating,
        notes=payload.notes,
        client_timestamp=payload.timestamp,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
