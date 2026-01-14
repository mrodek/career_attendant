from pydantic import BaseModel, Field
from typing import Optional, Literal, Any, List
from datetime import datetime, date


# === Job Schemas (shared job data) ===
# NOTE: We intentionally do NOT store raw job descriptions (legal/copyright concerns)
# Only derived/extracted signals are persisted

class JobBase(BaseModel):
    """Base schema for job data - only factual/derived fields, no raw content"""
    jobUrl: str
    jobTitle: Optional[str] = None
    companyName: Optional[str] = None
    # jobDescription intentionally omitted - not stored
    
    # Parsed compensation (extracted from page, not raw text)
    salaryMin: Optional[int] = None
    salaryMax: Optional[int] = None
    salaryCurrency: Optional[str] = "USD"
    salaryPeriod: Optional[Literal['year', 'hour', 'month', 'week']] = None
    salaryRaw: Optional[str] = None  # Display string only, e.g. "$150K-$200K/yr"
    
    # Location
    location: Optional[str] = None
    locationCountry: Optional[str] = None
    locationCity: Optional[str] = None
    
    # Work arrangement
    remoteType: Optional[Literal['onsite', 'hybrid', 'remote']] = None
    roleType: Optional[Literal['full_time', 'part_time', 'contract']] = None
    seniority: Optional[Literal['intern', 'junior', 'mid', 'senior', 'staff', 'principal', 'director', 'vp', 'cxo']] = None
    
    # Extracted skills (derived signals)
    requiredSkills: Optional[List[str]] = None
    preferredSkills: Optional[List[str]] = None
    yearsExperienceMin: Optional[int] = None
    yearsExperienceMax: Optional[int] = None
    
    # Metadata
    companyLogoUrl: Optional[str] = None
    industry: Optional[str] = None
    postingDate: Optional[date] = None
    expirationDate: Optional[date] = None
    easyApply: Optional[bool] = None
    source: Optional[str] = None
    extractionConfidence: Optional[int] = None  # 0-100


class JobOut(BaseModel):
    """Job output schema with all fields"""
    id: str
    jobUrl: str
    jobTitle: Optional[str] = None
    companyName: Optional[str] = None
    
    # Parsed compensation
    salaryMin: Optional[int] = None
    salaryMax: Optional[int] = None
    salaryCurrency: Optional[str] = None
    salaryPeriod: Optional[str] = None
    salaryRaw: Optional[str] = None
    
    # Location
    location: Optional[str] = None
    locationCountry: Optional[str] = None
    locationCity: Optional[str] = None
    
    # Work arrangement
    remoteType: Optional[str] = None
    roleType: Optional[str] = None
    seniority: Optional[str] = None
    
    # Extracted skills
    requiredSkills: Optional[List[str]] = None
    preferredSkills: Optional[List[str]] = None
    yearsExperienceMin: Optional[int] = None
    yearsExperienceMax: Optional[int] = None
    
    # Metadata
    companyLogoUrl: Optional[str] = None
    industry: Optional[str] = None
    postingDate: Optional[date] = None
    expirationDate: Optional[date] = None
    easyApply: Optional[bool] = None
    isActive: bool = True
    source: Optional[str] = None
    extractionConfidence: Optional[int] = None
    savedCount: int = 0
    
    # AI-Generated Content
    summary: Optional[str] = None
    summaryGeneratedAt: Optional[datetime] = None
    
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


# === SavedJob Schemas (user-specific tracking) ===

class SavedJobIn(BaseModel):
    """Input schema for saving a job - only derived/factual fields, no raw content"""
    # Job identification
    jobUrl: str
    jobTitle: Optional[str] = None
    companyName: Optional[str] = None
    
    # Parsed compensation (extracted client-side)
    salaryMin: Optional[int] = None
    salaryMax: Optional[int] = None
    salaryCurrency: Optional[str] = "USD"
    salaryPeriod: Optional[Literal['year', 'hour', 'month', 'week']] = None
    salaryRaw: Optional[str] = None
    
    # Location
    location: Optional[str] = None
    locationCountry: Optional[str] = None
    locationCity: Optional[str] = None
    
    # Work arrangement
    remoteType: Optional[Literal['onsite', 'hybrid', 'remote']] = None
    roleType: Optional[Literal['full_time', 'part_time', 'contract']] = None
    seniority: Optional[Literal['intern', 'junior', 'mid', 'senior', 'staff', 'principal', 'director', 'vp', 'cxo']] = None
    
    # Extracted skills (derived client-side from page content)
    requiredSkills: Optional[List[str]] = None
    preferredSkills: Optional[List[str]] = None
    yearsExperienceMin: Optional[int] = None
    yearsExperienceMax: Optional[int] = None
    
    # Metadata
    postingDate: Optional[date] = None
    easyApply: Optional[bool] = None
    source: Optional[str] = None
    extractionConfidence: Optional[int] = None  # 0-100
    
    # Debug (for debugging extraction - not for production use)
    scrapedTextDebug: Optional[str] = None  # Raw scraped text for debugging
    
    # LLM-generated content (from streaming extraction)
    summary: Optional[str] = None  # AI-generated job summary
    llmExtractedComprehensive: Optional[dict] = None  # Full comprehensive extraction JSON

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
