import uuid
from sqlalchemy import Column, String, Text, Enum, Boolean, SmallInteger, TIMESTAMP, ForeignKey, Date, JSON
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

class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Core job fields
    job_title = Column(String(500), nullable=True)
    company_name = Column(String(255), nullable=True)
    job_url = Column(Text, nullable=False)
    job_description = Column(Text, nullable=True)

    # Compensation & location
    salary_range = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)

    # Work arrangement and role type
    remote_type = Column(String(50), nullable=True)  # 'remote', 'hybrid', 'onsite'
    role_type = Column(String(50), nullable=True)    # 'full_time', 'part_time', 'contract'

    # Interest & application state
    interest_level = Column(String(20), nullable=True)  # 'high', 'medium', 'low'
    application_status = Column(String(50), nullable=False, server_default="saved")
    application_date = Column(Date, nullable=True)

    # Additional notes and scraped metadata
    notes = Column(Text, nullable=True)
    scraped_data = Column(JSON, nullable=True)
    source = Column(String(100), nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="saved_jobs")
