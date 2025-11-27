import uuid
from sqlalchemy import Column, String, Text, Enum, Boolean, SmallInteger, TIMESTAMP, ForeignKey
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    entries = relationship("Entry", back_populates="user")

class Entry(Base):
    __tablename__ = "entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    url = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    company = Column(Text, nullable=True)
    work_type = Column(Enum(WorkType), nullable=True)
    salary_range = Column(Enum(SalaryRange), nullable=True)
    job_type = Column(Enum(JobType), nullable=True)
    location = Column(Text, nullable=True)
    applied = Column(Boolean, nullable=True)

    user_email = Column(Text, nullable=True)
    user_identity_id = Column(Text, nullable=True)

    rating = Column(SmallInteger, nullable=True)
    notes = Column(Text, nullable=True)

    client_timestamp = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="entries")
