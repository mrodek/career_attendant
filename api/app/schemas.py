from pydantic import BaseModel, Field
from typing import Optional, Literal, Any, List
from datetime import datetime, date


# === Job Schemas (shared job data) ===

class JobBase(BaseModel):
    """Base schema for job data"""
    jobUrl: str
    jobTitle: Optional[str] = None
    companyName: Optional[str] = None
    jobDescription: Optional[str] = None
    salaryRange: Optional[str] = None
    location: Optional[str] = None
    remoteType: Optional[Literal['onsite', 'hybrid', 'remote']] = None
    roleType: Optional[Literal['full_time', 'part_time', 'contract']] = None
    experienceLevel: Optional[Literal['entry', 'mid', 'senior', 'lead', 'executive']] = None
    companyLogoUrl: Optional[str] = None
    industry: Optional[str] = None
    requiredSkills: Optional[List[str]] = None
    postingDate: Optional[date] = None
    expirationDate: Optional[date] = None
    source: Optional[str] = None
    scrapedData: Optional[Any] = None


class JobOut(BaseModel):
    """Job output schema with all fields"""
    id: str
    jobUrl: str
    jobTitle: Optional[str] = None
    companyName: Optional[str] = None
    jobDescription: Optional[str] = None
    salaryRange: Optional[str] = None
    location: Optional[str] = None
    remoteType: Optional[str] = None
    roleType: Optional[str] = None
    experienceLevel: Optional[str] = None
    companyLogoUrl: Optional[str] = None
    industry: Optional[str] = None
    requiredSkills: Optional[List[str]] = None
    postingDate: Optional[date] = None
    expirationDate: Optional[date] = None
    isActive: bool = True
    source: Optional[str] = None
    savedCount: int = 0
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


# === SavedJob Schemas (user-specific tracking) ===

class SavedJobIn(BaseModel):
    """Input schema for saving a job - includes job data for creation"""
    # Job fields (used to find or create the Job)
    jobUrl: str
    jobTitle: Optional[str] = None
    companyName: Optional[str] = None
    jobDescription: Optional[str] = None
    salaryRange: Optional[str] = None
    location: Optional[str] = None
    remoteType: Optional[Literal['onsite', 'hybrid', 'remote']] = None
    roleType: Optional[Literal['full_time', 'part_time', 'contract']] = None
    experienceLevel: Optional[Literal['entry', 'mid', 'senior', 'lead', 'executive']] = None
    source: Optional[str] = None
    scrapedData: Optional[Any] = None

    # User-specific tracking fields
    interestLevel: Optional[Literal['high', 'medium', 'low']] = None
    applicationStatus: Optional[Literal['saved', 'applied', 'interviewing', 'rejected', 'offer']] = 'saved'
    applicationDate: Optional[date] = None
    notes: Optional[str] = None
    reminderDate: Optional[date] = None
    priorityRank: Optional[int] = None

    # Legacy fields (accepted but not stored directly)
    userEmail: Optional[str] = None
    userId: Optional[str] = None


class SavedJobOut(BaseModel):
    """Output schema for a saved job with nested job data"""
    id: str
    job: JobOut

    # User-specific tracking
    interestLevel: Optional[str] = None
    applicationStatus: str = 'saved'
    applicationDate: Optional[date] = None
    notes: Optional[str] = None
    reminderDate: Optional[date] = None
    priorityRank: Optional[int] = None

    # Application outcome
    rejectionReason: Optional[str] = None
    interviewDates: Optional[List[dict]] = None
    salaryOffered: Optional[str] = None
    referralContact: Optional[str] = None

    # AI Job Fit Assessment
    jobFitScore: Optional[Literal['weak', 'fair', 'good', 'strong', 'very_strong']] = None
    jobFitReason: Optional[str] = None
    jobFitAssessedAt: Optional[datetime] = None

    # AI-Generated Documents
    targetedResumeUrl: Optional[str] = None
    targetedCoverLetterUrl: Optional[str] = None
    documentsGeneratedAt: Optional[datetime] = None

    # Workflow status
    aiWorkflowStatus: Optional[Literal['pending', 'assessing', 'generating', 'completed', 'failed']] = None
    aiWorkflowError: Optional[str] = None

    # Timestamps
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class SavedJobUpdate(BaseModel):
    """Schema for updating a saved job"""
    interestLevel: Optional[Literal['high', 'medium', 'low']] = None
    applicationStatus: Optional[Literal['saved', 'applied', 'interviewing', 'rejected', 'offer']] = None
    applicationDate: Optional[date] = None
    notes: Optional[str] = None
    reminderDate: Optional[date] = None
    priorityRank: Optional[int] = None
    rejectionReason: Optional[str] = None
    salaryOffered: Optional[str] = None
    referralContact: Optional[str] = None


# === Legacy Aliases for Backward Compatibility ===

# EntryIn is now an alias for SavedJobIn
EntryIn = SavedJobIn


class EntryOut(BaseModel):
    """Legacy output schema - minimal response after creation"""
    id: str
    created_at: datetime


class EntriesOut(BaseModel):
    """Paginated list of saved jobs"""
    items: List[dict]
    total: int
    page: int
    pageSize: int


# === Job List Schemas ===

class JobsOut(BaseModel):
    """Paginated list of jobs (for recommendations, etc.)"""
    items: List[JobOut]
    total: int
    page: int
    pageSize: int
