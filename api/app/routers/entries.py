from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..db import get_db
from ..schemas import EntryIn, EntryOut, EntriesOut
from ..crud import upsert_user_by_email, create_entry
from ..config import Settings
from ..models import SavedJob

router = APIRouter(prefix="/entries", tags=["entries"])

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    settings = Settings()
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

@router.post("/", response_model=EntryOut, dependencies=[Depends(verify_api_key)])
async def create_entry_route(payload: EntryIn, db: Session = Depends(get_db)):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Received entry creation request for URL: {payload.jobUrl}")
    
    user = upsert_user_by_email(db, payload.userEmail)
    logger.info(f"User: {user.email if user else 'None'}")
    
    entry = create_entry(db, user, payload)
    logger.info(f"Entry created with ID: {entry.id}")
    
    db.commit()  # Explicitly commit the transaction
    logger.info(f"Entry committed to database")
    
    return {"id": str(entry.id), "created_at": entry.created_at}

@router.get("/", response_model=EntriesOut, dependencies=[Depends(verify_api_key)])
async def list_entries(
    db: Session = Depends(get_db),
    userId: Optional[str] = Query(default=None),
    jobUrl: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
):
    # Build ORM query
    q = db.query(SavedJob)
    if userId:
        # Filter by user_id (UUID) if provided
        try:
            from uuid import UUID
            user_uuid = UUID(userId)
            q = q.filter(SavedJob.user_id == user_uuid)
        except (ValueError, AttributeError):
            pass  # Invalid UUID, skip filter
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
