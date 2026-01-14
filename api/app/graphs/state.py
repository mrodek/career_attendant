"""
Graph state definitions for Job Intake & Analysis pipeline.

The state flows through each node, accumulating data as it progresses.
"""

from typing import TypedDict, Optional, List, Any
from datetime import datetime


class JobDocPartial(TypedDict, total=False):
    """Extracted job document fields (may be partial during processing)."""
    job_url: str
    job_title: Optional[str]
    company_name: Optional[str]
    
    # Salary
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_currency: Optional[str]
    salary_period: Optional[str]
    salary_raw: Optional[str]
    
    # Location
    location: Optional[str]
    location_country: Optional[str]
    location_city: Optional[str]
    
    # Work arrangement
    remote_type: Optional[str]
    role_type: Optional[str]
    seniority: Optional[str]
    
    # Skills
    required_skills: Optional[List[str]]
    preferred_skills: Optional[List[str]]
    years_experience_min: Optional[int]
    years_experience_max: Optional[int]
    
    # Metadata
    source: Optional[str]
    easy_apply: Optional[bool]
    posting_date: Optional[str]


class SegmentedText(TypedDict, total=False):
    """Segmented job description sections."""
    full_text: str
    about: Optional[str]
    responsibilities: Optional[str]
    requirements: Optional[str]
    qualifications: Optional[str]
    benefits: Optional[str]
    company_info: Optional[str]


class DocStats(TypedDict, total=False):
    """Document statistics for the scraped content."""
    char_count: int
    word_count: int
    token_count: int
    section_count: int
    language: str


class JobIntakeState(TypedDict, total=False):
    """
    Complete state for the Job Intake & Analysis graph.
    
    Each node reads from and writes to this state.
    """
    # === Input (from extension) ===
    job_id: str  # UUID of existing job record
    job_url: str
    raw_text: str  # scraped_text_debug from extension
    extension_extracted: JobDocPartial  # What the extension already extracted
    
    # === Node 1: ingest_raw_capture ===
    thread_id: str  # Unique ID for this analysis run
    ingested_at: str  # ISO timestamp
    
    # === Node 2: preprocess_and_segment ===
    segmented: SegmentedText
    doc_stats: DocStats
    
    # === Node 3: extract_structured_fields ===
    llm_extracted: JobDocPartial  # LLM-extracted fields (legacy, for backward compatibility)
    extraction_evidence: List[dict]  # Evidence for each extraction
    comprehensive_analysis: dict  # Full JSON output from comprehensive extraction prompt
    
    # === Node 4: normalize_and_validate (future) ===
    jobdoc: JobDocPartial  # Final merged + validated JobDoc
    validation_errors: List[str]
    confidence_scores: dict
    
    # === Node 5: generate_job_summary ===
    job_summary: str  # 6-10 bullet summary
    success_criteria: str  # "What success looks like"
    
    # === Node 6: persist_job_artifacts ===
    persisted: bool
    embedding_id: Optional[str]  # ChromaDB document ID
    
    # === Error handling ===
    errors: List[str]
    current_node: str
