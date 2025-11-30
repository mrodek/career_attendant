from pydantic import BaseModel, Field
from typing import Optional, Literal, Any
from datetime import datetime, date


class EntryIn(BaseModel):
    # Core job details
    jobUrl: str
    jobTitle: Optional[str] = None
    companyName: Optional[str] = None
    jobDescription: Optional[str] = None

    # Compensation & location
    salaryRange: Optional[str] = None
    location: Optional[str] = None

    # Work arrangement and role type
    remoteType: Optional[Literal['onsite', 'hybrid', 'remote']] = None
    roleType: Optional[Literal['full_time', 'part_time', 'contract']] = None

    # Interest & application state
    interestLevel: Optional[Literal['high', 'medium', 'low']] = None
    applicationStatus: Optional[Literal['saved', 'applied', 'interviewing', 'rejected', 'offer']] = 'saved'
    applicationDate: Optional[date] = None

    # User association (still accepted but no longer stored as columns)
    userEmail: Optional[str] = None
    userId: Optional[str] = None

    # Free-form notes and extra metadata
    notes: Optional[str] = None
    source: Optional[str] = None
    scrapedData: Optional[Any] = None


class EntryOut(BaseModel):
    id: str
    created_at: datetime


class EntriesOut(BaseModel):
    items: list[dict]
    total: int
    page: int
    pageSize: int
