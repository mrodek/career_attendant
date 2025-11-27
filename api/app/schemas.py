from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime

class EntryIn(BaseModel):
    url: str
    title: Optional[str] = None
    company: Optional[str] = None
    workType: Optional[Literal['OnSite','Hybrid','Remote']] = None
    salaryRange: Optional[Literal['Unknown','>$200K','$200-300K','$300-400K','$400+K']] = None
    jobType: Optional[Literal['Full-Time','Part-Time','Contract']] = None
    location: Optional[str] = None
    applied: Optional[bool] = None
    userEmail: Optional[str] = None
    userId: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    notes: Optional[str] = None
    timestamp: Optional[datetime] = None

class EntryOut(BaseModel):
    id: str
    created_at: datetime

class EntriesOut(BaseModel):
    items: list[dict]
    total: int
    page: int
    pageSize: int
