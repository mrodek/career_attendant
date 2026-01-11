from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from uuid import UUID
from ..db import get_db
from ..schemas import EntryIn, EntryOut, EntriesOut, SavedJobUpdate
from ..crud import upsert_user_by_email, create_entry, get_saved_job_by_url
from ..config import Settings
from ..models import SavedJob, Job, User
from ..auth.dependencies import get_current_user, get_current_user_id
from ..logger import logger

router = APIRouter(prefix="/entries", tags=["entries"])


@router.get("/check-by-url")
async def check_job_by_url(
    url: str = Query(..., description="Job URL to check"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Check if a job exists for the current user by URL.
    Returns job data if exists, avoiding redundant extraction.
    
    This is used by the browser extension to avoid re-extracting
    jobs that have already been saved.
    """
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL parameter is required")
        
        logger.info(f"Checking if job exists for user {user_id}: {url}")
        
        # For LinkedIn, extract the job ID from currentJobId parameter
        # Otherwise, normalize URL (remove trailing slash, query params, fragments)
        if 'linkedin.com' in url and 'currentJobId=' in url:
            # Extract job ID from LinkedIn URL
            import re
            match = re.search(r'currentJobId=(\d+)', url)
            if match:
                job_id = match.group(1)
                # Search for any job URL containing this job ID (join with Job table)
                saved_job = db.query(SavedJob).join(Job).filter(
                    SavedJob.user_id == user_id,
                    Job.job_url.like(f"%currentJobId={job_id}%")
                ).first()
            else:
                normalized_url = url.rstrip('/').split('?')[0].split('#')[0]
                saved_job = db.query(SavedJob).join(Job).filter(
                    SavedJob.user_id == user_id,
                    Job.job_url.like(f"{normalized_url}%")
                ).first()
        else:
            # For other sites, use normalized URL
            normalized_url = url.rstrip('/').split('?')[0].split('#')[0]
            saved_job = db.query(SavedJob).join(Job).filter(
                SavedJob.user_id == user_id,
                Job.job_url.like(f"{normalized_url}%")
            ).first()
        
        logger.info(f"SavedJob found: {saved_job is not None}")
        
        if not saved_job:
            return {
                "exists": False,
                "job_id": None,
                "has_extraction": False,
                "has_summary": False,
                "job_data": None
            }
        
        # Access the related Job object
        job = saved_job.job
        
        # Check if extraction and summary exist (in Job table)
        has_extraction = bool(job.required_skills or job.salary_min or job.seniority)
        has_summary = bool(job.summary and len(job.summary) > 0)
        
        return {
            "exists": True,
            "job_id": str(saved_job.id),
            "has_extraction": has_extraction,
            "has_summary": has_summary,
            "job_data": {
                "id": str(saved_job.id),
                "title": job.job_title,
                "company": job.company_name,
                "location": job.location,
                "job_url": job.job_url,
                "interest_level": saved_job.interest_level,
                "status": saved_job.application_status,
                "extracted_data": {
                    "jobTitle": job.job_title,
                    "companyName": job.company_name,
                    "location": job.location,
                    "salaryMin": job.salary_min,
                    "salaryMax": job.salary_max,
                    "remoteType": job.remote_type,
                    "roleType": job.role_type,
                    "seniority": job.seniority,
                    "required_skills": job.required_skills or [],
                },
                "ai_summary": job.summary,
                "created_at": saved_job.created_at.isoformat() if saved_job.created_at else None,
                "updated_at": saved_job.updated_at.isoformat() if saved_job.updated_at else None
            }
        }
    except Exception as e:
        logger.error(f"Error checking job by URL: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check job: {str(e)}"
        )


async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Legacy API key verification - kept for backward compatibility"""
    settings = Settings()
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.post("", response_model=EntryOut)
async def create_entry_route(
    payload: EntryIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job entry for the authenticated user"""
    logger.info(f"Received entry creation request for URL: {payload.jobUrl} from user: {user.id}")
    
    # Check if user already saved this job
    existing = get_saved_job_by_url(db, user.id, payload.jobUrl)
    if existing:
        raise HTTPException(
            status_code=409,
            detail="You have already saved this job."
        )
    
    # Check subscription limits for free tier
    if user.subscription_tier == "free":
        job_count = db.query(SavedJob).filter_by(user_id=user.id).count()
        if job_count >= 100:
            raise HTTPException(
                status_code=403,
                detail="Free tier limit reached (100 jobs). Upgrade to save more jobs."
            )
    
    try:
        entry = create_entry(db, user, payload)
        logger.info(f"Entry created with ID: {entry.id}")
        
        db.commit()
        logger.info(f"Entry committed to database")
        
        return {"id": str(entry.id), "created_at": entry.created_at}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="You have already saved this job."
        )


@router.get("/", response_model=EntriesOut)
async def list_entries(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    jobUrl: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
):
    """List job entries for the authenticated user (row-level security)"""
    # Build ORM query with Job join - always filter by authenticated user
    q = (
        db.query(SavedJob, Job)
        .join(Job, SavedJob.job_id == Job.id)
        .filter(SavedJob.user_id == user_id)
    )
    
    if jobUrl:
        q = q.filter(Job.job_url == jobUrl)

    total = q.count()
    items = (
        q.order_by(SavedJob.created_at.desc())
         .offset((page - 1) * pageSize)
         .limit(pageSize)
         .all()
    )

    out_items = [
        {
            "id": str(saved.id),
            # Nested job data (new schema with parsed fields)
            "job": {
                "id": str(job.id),
                "jobUrl": job.job_url,
                "jobTitle": job.job_title,
                "companyName": job.company_name,
                # Parsed salary fields
                "salaryMin": job.salary_min,
                "salaryMax": job.salary_max,
                "salaryCurrency": job.salary_currency,
                "salaryPeriod": job.salary_period,
                "salaryRaw": job.salary_raw,
                # Location
                "location": job.location,
                "locationCountry": job.location_country,
                "locationCity": job.location_city,
                # Work arrangement
                "remoteType": job.remote_type,
                "roleType": job.role_type,
                "seniority": job.seniority,
                # Extracted skills
                "requiredSkills": job.required_skills,
                "preferredSkills": job.preferred_skills,
                "yearsExperienceMin": job.years_experience_min,
                "yearsExperienceMax": job.years_experience_max,
                # Metadata
                "companyLogoUrl": job.company_logo_url,
                "industry": job.industry,
                "postingDate": job.posting_date,
                "expirationDate": job.expiration_date,
                "easyApply": job.easy_apply,
                "isActive": job.is_active,
                "source": job.source,
                "extractionConfidence": job.extraction_confidence,
                "savedCount": job.saved_count,
                # AI-Generated Content
                "summary": job.summary,
                "summaryGeneratedAt": job.summary_generated_at,
                # Timestamps
                "createdAt": job.created_at,
                "updatedAt": job.updated_at,
            },
            # Flattened for backward compatibility
            "jobUrl": job.job_url,
            "jobTitle": job.job_title,
            "companyName": job.company_name,
            "location": job.location,
            "salaryRaw": job.salary_raw,  # Display string
            "remoteType": job.remote_type,
            "roleType": job.role_type,
            # User-specific tracking
            "interestLevel": saved.interest_level,
            "applicationStatus": saved.application_status,
            "applicationDate": saved.application_date,
            "notes": saved.notes,
            "reminderDate": saved.reminder_date,
            "priorityRank": saved.priority_rank,
            # Application outcome
            "rejectionReason": saved.rejection_reason,
            "interviewDates": saved.interview_dates,
            "salaryOffered": saved.salary_offered,
            "referralContact": saved.referral_contact,
            # AI Assessment
            "jobFitScore": saved.job_fit_score,
            "jobFitReason": saved.job_fit_reason,
            "jobFitAssessedAt": saved.job_fit_assessed_at,
            # AI Documents
            "targetedResumeUrl": saved.targeted_resume_url,
            "targetedCoverLetterUrl": saved.targeted_cover_letter_url,
            "documentsGeneratedAt": saved.documents_generated_at,
            # Workflow
            "aiWorkflowStatus": saved.ai_workflow_status,
            "aiWorkflowError": saved.ai_workflow_error,
            # Timestamps
            "created_at": saved.created_at,
            "updated_at": saved.updated_at,
        }
        for saved, job in items
    ]
    return {"items": out_items, "total": total, "page": page, "pageSize": pageSize}


@router.patch("/{entry_id}")
async def update_entry(
    entry_id: str,
    payload: SavedJobUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update a saved job entry for the authenticated user"""
    # Convert string IDs to UUID
    try:
        entry_uuid = UUID(entry_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Find the saved job and verify ownership
    saved_job = db.query(SavedJob).filter(
        SavedJob.id == entry_uuid,
        SavedJob.user_id == user_id
    ).first()
    
    if not saved_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update only the fields that were provided
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Convert camelCase to snake_case for model attributes
        snake_field = ''.join(['_' + c.lower() if c.isupper() else c for c in field]).lstrip('_')
        if hasattr(saved_job, snake_field):
            setattr(saved_job, snake_field, value)
    
    db.commit()
    db.refresh(saved_job)
    
    logger.info(f"Updated entry {entry_id} for user {user_id}")
    
    return {"id": str(saved_job.id), "updated": True}


@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a saved job entry for the authenticated user"""
    # Convert string IDs to UUID
    try:
        entry_uuid = UUID(entry_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Find the saved job and verify ownership
    saved_job = db.query(SavedJob).filter(
        SavedJob.id == entry_uuid,
        SavedJob.user_id == user_id
    ).first()
    
    if not saved_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Decrement the job's saved_count
    job = db.query(Job).filter(Job.id == saved_job.job_id).first()
    if job and job.saved_count and job.saved_count > 0:
        job.saved_count -= 1
    
    db.delete(saved_job)
    db.commit()
    
    logger.info(f"Deleted entry {entry_id} for user {user_id}")
    
    return {"id": entry_id, "deleted": True}
