from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..db import get_db
from ..schemas import EntryIn, EntryOut, EntriesOut
from ..crud import upsert_user_by_email, create_entry
from ..config import Settings
from ..models import Entry

router = APIRouter(prefix="/entries", tags=["entries"])

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    settings = Settings()
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

@router.post("/", response_model=EntryOut, dependencies=[Depends(verify_api_key)])
async def create_entry_route(payload: EntryIn, db: Session = Depends(get_db)):
    user = upsert_user_by_email(db, payload.userEmail)
    entry = create_entry(db, user, payload)
    return {"id": str(entry.id), "created_at": entry.created_at}

@router.get("/", response_model=EntriesOut, dependencies=[Depends(verify_api_key)])
async def list_entries(
    db: Session = Depends(get_db),
    userEmail: Optional[str] = Query(default=None),
    url: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=200),
):
    # Build ORM query
    q = db.query(Entry)
    if userEmail:
        q = q.filter(Entry.user_email == userEmail)
    if url:
        q = q.filter(Entry.url == url)

    total = q.count()
    items = (
        q.order_by(Entry.created_at.desc())
         .offset((page - 1) * pageSize)
         .limit(pageSize)
         .all()
    )

    out_items = [
        {
            "id": str(i.id),
            "url": i.url,
            "title": i.title,
            "company": i.company,
            "created_at": i.created_at,
            "user_email": i.user_email,
        }
        for i in items
    ]
    return {"items": out_items, "total": total, "page": page, "pageSize": pageSize}
