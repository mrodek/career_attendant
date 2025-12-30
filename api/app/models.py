import uuid
from sqlalchemy import Column, String, Text, Enum, Boolean, SmallInteger, Integer, TIMESTAMP, ForeignKey, Date, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .db import Base
import enum

class WorkType(str, enum.Enum):
    OnSite = "OnSite"
    Hybrid = "Hybrid"
    Remote = "Remote"

class SalaryRange(str, enum.Enum):
    Unknown = "Unknown"
    GT200 = ">$200K"
    R200_300 = "$200-300K"
    R300_400 = "$300-400K"
    GT400 = "$400+K"

class JobType(str, enum.Enum):
    FullTime = "Full-Time"
    PartTime = "Part-Time"
    Contract = "Contract"

class User(Base):
    __tablename__ = "users"

    id = Column(String(255), primary_key=True)  # Clerk user_id or Chrome profile ID
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    subscription_tier = Column(String(50), nullable=False, server_default="free")
    subscription_status = Column(String(50), nullable=False, server_default="active")
    stripe_customer_id = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    user_metadata = Column(JSON, nullable=True, server_default="{}")

    saved_jobs = relationship("SavedJob", back_populates="user")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    feature_access = relationship("FeatureAccess", back_populates="user", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # === Core Job Fields (Factual, non-copyrightable) ===
    job_title = Column(String(500), nullable=True)
    company_name = Column(String(255), nullable=True)
    job_url = Column(Text, nullable=False, unique=True, index=True)
    # NOTE: job_description intentionally not stored (legal/copyright concerns)

    # === Parsed Compensation ===
    salary_min = Column(Integer, nullable=True)           # Parsed: 150000
    salary_max = Column(Integer, nullable=True)           # Parsed: 200000
    salary_currency = Column(String(10), nullable=True, server_default="USD")
    salary_period = Column(String(20), nullable=True)     # 'year', 'hour', 'month'
    salary_raw = Column(String(100), nullable=True)       # "$150K-$200K/yr" (display string only)

    # === Location ===
    location = Column(String(255), nullable=True)
    location_country = Column(String(10), nullable=True)  # 'US', 'CA', etc.
    location_city = Column(String(100), nullable=True)

    # === Work Arrangement & Role Type ===
    remote_type = Column(String(50), nullable=True)       # 'remote', 'hybrid', 'onsite'
    role_type = Column(String(50), nullable=True)         # 'full_time', 'part_time', 'contract'
    seniority = Column(String(50), nullable=True)         # 'intern', 'junior', 'mid', 'senior', 'staff', 'principal', 'director', 'vp', 'cxo'

    # === Extracted Skills (Derived signals, not raw content) ===
    required_skills = Column(JSON, nullable=True)         # ["Python", "Kubernetes", "PyTorch"]
    preferred_skills = Column(JSON, nullable=True)        # ["Go", "Terraform"]
    years_experience_min = Column(SmallInteger, nullable=True)
    years_experience_max = Column(SmallInteger, nullable=True)

    # === Job Metadata ===
    company_logo_url = Column(String(500), nullable=True)
    industry = Column(String(100), nullable=True)
    posting_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    easy_apply = Column(Boolean, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")

    # === Source & Extraction Metadata ===
    source = Column(String(100), nullable=True)           # 'linkedin', 'indeed', 'greenhouse'
    extracted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    extraction_confidence = Column(Integer, nullable=True)  # 0-100 confidence score

    # === Debug Data (for extraction debugging, not for production use) ===
    scraped_text_debug = Column(Text, nullable=True)  # Raw scraped text for debugging extraction

    # === Analytics ===
    saved_count = Column(Integer, nullable=False, server_default="0")

    # === Timestamps ===
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # === Relationships ===
    user_jobs = relationship("SavedJob", back_populates="job")

class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    # === Interest & Application State ===
    interest_level = Column(String(20), nullable=True)                              # 'high', 'medium', 'low'
    application_status = Column(String(50), nullable=False, server_default="saved") # 'saved', 'applied', 'interviewing', 'rejected', 'offer'
    application_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    # === User Organization ===
    reminder_date = Column(Date, nullable=True)
    priority_rank = Column(SmallInteger, nullable=True)

    # === Application Outcome ===
    rejection_reason = Column(String(255), nullable=True)
    interview_dates = Column(JSON, nullable=True)         # [{"date": "2024-01-15", "type": "phone"}, ...]
    salary_offered = Column(String(100), nullable=True)
    referral_contact = Column(String(255), nullable=True)

    # === AI Job Fit Assessment ===
    job_fit_score = Column(String(20), nullable=True)     # 'weak', 'fair', 'good', 'strong', 'very_strong'
    job_fit_reason = Column(Text, nullable=True)
    job_fit_assessed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # === AI-Generated Documents ===
    targeted_resume_url = Column(String(1000), nullable=True)
    targeted_resume_drive_id = Column(String(100), nullable=True)
    targeted_cover_letter_url = Column(String(1000), nullable=True)
    targeted_cover_letter_drive_id = Column(String(100), nullable=True)
    documents_generated_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # === AI Workflow Status ===
    ai_workflow_status = Column(String(50), nullable=True)  # 'pending', 'assessing', 'generating', 'completed', 'failed'
    ai_workflow_error = Column(Text, nullable=True)

    # === Timestamps ===
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # === Constraints ===
    __table_args__ = (
        UniqueConstraint('user_id', 'job_id', name='uq_user_job'),
    )

    # === Relationships ===
    user = relationship("User", back_populates="saved_jobs")
    job = relationship("Job", back_populates="user_jobs")

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)

    user = relationship("User", back_populates="sessions")

class FeatureAccess(Base):
    __tablename__ = "feature_access"

    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    feature_name = Column(String(100), primary_key=True)
    access_granted = Column(Boolean, nullable=False, server_default="false")
    usage_count = Column(SmallInteger, nullable=False, server_default="0")
    usage_limit = Column(SmallInteger, nullable=True)
    reset_period = Column(String(50), nullable=True)  # 'daily', 'weekly', 'monthly'
    last_reset = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="feature_access")
