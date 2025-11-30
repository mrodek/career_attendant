from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..db import get_db
from ..schemas import EntryIn, EntryOut, EntriesOut
from ..crud import upsert_user_by_email, create_entry
from ..config import Settings
from ..models import SavedJob, User
from ..auth.dependencies import get_current_user, get_current_user_id
from ..logger import logger

router = APIRouter(prefix="/entries", tags=["entries"])

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
    
    # Check subscription limits for free tier
    if user.subscription_tier == "free":
        job_count = db.query(SavedJob).filter_by(user_id=user.id).count()
        if job_count >= 100:
            raise HTTPException(
                status_code=403,
                detail="Free tier limit reached (100 jobs). Upgrade to save more jobs."
            )
    
    entry = create_entry(db, user, payload)
    logger.info(f"Entry created with ID: {entry.id}")
    
    db.commit()
    logger.info(f"Entry committed to database")
    
    return {"id": str(entry.id), "created_at": entry.created_at}

@router.get("/", response_model=EntriesOut)
async def list_entries(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    jobUrl: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
):
    """List job entries for the authenticated user (row-level security)"""
    # Build ORM query - always filter by authenticated user
    q = db.query(SavedJob).filter(SavedJob.user_id == user_id)
    
    if jobUrl:
        q = q.filter(SavedJob.job_url == jobUrl)

    total = q.count()
    items = (
        q.order_by(SavedJob.created_at.desc())
         .offset((page - 1) * pageSize)
         .limit(pageSize)
         .all()
    )

    out_items = [
        {
            "id": str(i.id),
            "jobUrl": i.job_url,
            "jobTitle": i.job_title,
            "companyName": i.company_name,
            "location": i.location,
            "applicationStatus": i.application_status,
            "interestLevel": i.interest_level,
            "created_at": i.created_at,
            "updated_at": i.updated_at,
        }
        for i in items
    ]
    return {"items": out_items, "total": total, "page": page, "pageSize": pageSize}
