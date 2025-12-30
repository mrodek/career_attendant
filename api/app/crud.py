from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models
from .models import User, SavedJob, Job
from .schemas import EntryIn
from typing import Optional, Tuple

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
def get_or_create_job(db: Session, payload: EntryIn) -> Tuple[Job, bool]:
    """
    Find an existing job by URL or create a new one.
    Returns: (job, created) where created is True if a new job was created.
    """
    # Try to find existing job by URL
    job = db.query(Job).filter(Job.job_url == payload.jobUrl).one_or_none()
    if job:
        # Optionally update job metadata if new data is more complete
        updated = False
        if payload.jobTitle and not job.job_title:
            job.job_title = payload.jobTitle
            updated = True
        if payload.companyName and not job.company_name:
            job.company_name = payload.companyName
            updated = True
        if payload.jobDescription and not job.job_description:
            job.job_description = payload.jobDescription
            updated = True
        if payload.salaryRange and not job.salary_range:
            job.salary_range = payload.salaryRange
            updated = True
        if payload.location and not job.location:
            job.location = payload.location
            updated = True
        if payload.remoteType and not job.remote_type:
            job.remote_type = payload.remoteType
            updated = True
        if payload.roleType and not job.role_type:
            job.role_type = payload.roleType
            updated = True
        if payload.experienceLevel and not job.experience_level:
            job.experience_level = payload.experienceLevel
            updated = True
        if payload.source and not job.source:
            job.source = payload.source
            updated = True
        if payload.scrapedData and not job.scraped_data:
            job.scraped_data = payload.scrapedData
            updated = True
        
        if updated:
            db.flush()
        
        return job, False
    
    # Create new job
    job = Job(
        job_url=payload.jobUrl,
        job_title=payload.jobTitle,
        company_name=payload.companyName,
        job_description=payload.jobDescription,
        salary_range=payload.salaryRange,
        location=payload.location,
        remote_type=payload.remoteType,
        role_type=payload.roleType,
        experience_level=getattr(payload, 'experienceLevel', None),
        source=payload.source,
        scraped_data=payload.scrapedData,
    )
    db.add(job)
    db.flush()
    return job, True


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.2, max=2))
def create_entry(db: Session, user: User, payload: EntryIn) -> SavedJob:
    """
    Save a job for a user. Creates the job if it doesn't exist.
    Raises IntegrityError if the user has already saved this job.
    """
    # Get or create the job
    job, job_created = get_or_create_job(db, payload)
    
    # Create the user-job association
    saved_job = SavedJob(
        user_id=user.id,
        job_id=job.id,
        interest_level=payload.interestLevel,
        application_status=payload.applicationStatus or 'saved',
        application_date=payload.applicationDate,
        notes=payload.notes,
        reminder_date=getattr(payload, 'reminderDate', None),
        priority_rank=getattr(payload, 'priorityRank', None),
    )
    db.add(saved_job)
    
    # Increment saved_count on the job
    job.saved_count = (job.saved_count or 0) + 1
    
    db.flush()
    return saved_job


def get_saved_job_by_url(db: Session, user_id: str, job_url: str) -> Optional[SavedJob]:
    """
    Check if a user has already saved a job by its URL.
    """
    return (
        db.query(SavedJob)
        .join(Job, SavedJob.job_id == Job.id)
        .filter(SavedJob.user_id == user_id)
        .filter(Job.job_url == job_url)
        .one_or_none()
    )


def get_job_by_url(db: Session, job_url: str) -> Optional[Job]:
    """
    Find a job by its URL.
    """
    return db.query(Job).filter(Job.job_url == job_url).one_or_none()
