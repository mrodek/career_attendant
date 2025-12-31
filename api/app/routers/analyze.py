"""
API routes for job analysis (LangGraph pipelines).

These endpoints trigger the AI-powered analysis of saved jobs.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import UUID

from ..db import get_db
from ..models import Job, SavedJob
from ..auth.dependencies import get_current_user_id
from ..logger import logger

router = APIRouter(prefix="/analyze", tags=["analyze"])


class AnalyzeJobRequest(BaseModel):
    """Request to analyze a job."""
    job_id: str


class AnalyzeJobResponse(BaseModel):
    """Response from job analysis."""
    job_id: str
    status: str  # "started", "completed", "failed"
    summary: Optional[str] = None
    extraction_evidence: Optional[List[dict]] = None
    errors: Optional[List[str]] = None


def run_analysis_background(
    job_id: str,
    job_url: str,
    raw_text: str,
    extension_extracted: Dict[str, Any],
    db_url: str,
):
    """
    Background task to run job analysis.
    
    This runs in a separate thread to avoid blocking the API.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from ..graphs import run_job_intake
    import asyncio
    
    # Create new DB session for background task
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Run the graph synchronously
        from ..graphs.job_intake_graph import run_job_intake_sync
        
        logger.info(f"Running analysis with raw_text length: {len(raw_text)}, extension_extracted keys: {list(extension_extracted.keys())}")
        
        result = run_job_intake_sync(
            job_id=job_id,
            job_url=job_url,
            raw_text=raw_text,
            extension_extracted=extension_extracted,
            db=db,
        )
        
        # Commit any changes
        db.commit()
        
        # Debug: Log the full result
        logger.info(f"Job analysis completed for {job_id}: persisted={result.get('persisted')}")
        logger.info(f"  - Errors: {result.get('errors', [])}")
        logger.info(f"  - Summary length: {len(result.get('job_summary', '') or '')}")
        logger.info(f"  - Current node: {result.get('current_node')}")
        
    except Exception as e:
        logger.error(f"Job analysis failed for {job_id}: {str(e)}")
        db.rollback()
    finally:
        db.close()


@router.post("/{job_id}", response_model=AnalyzeJobResponse)
async def analyze_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Trigger AI analysis for a saved job.
    
    This endpoint:
    1. Validates the job exists and belongs to the user
    2. Starts the LangGraph pipeline in the background
    3. Returns immediately with status "started"
    
    The analysis runs asynchronously and updates the job record when complete.
    """
    from ..config import Settings
    
    # Validate job_id
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    # Check if user has access to this job
    # The job_id parameter can be either saved_job.id OR job.id
    saved_job = db.query(SavedJob).filter(
        SavedJob.id == job_uuid,
        SavedJob.user_id == user_id,
    ).first()
    
    # Fallback: try job_id if not found by saved_job.id
    if not saved_job:
        saved_job = db.query(SavedJob).filter(
            SavedJob.job_id == job_uuid,
            SavedJob.user_id == user_id,
        ).first()
    
    if not saved_job:
        raise HTTPException(status_code=404, detail="Job not found or not saved by user")
    
    # Get the job record via the saved_job relationship
    job = saved_job.job
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if already analyzed
    if job.summary:
        return AnalyzeJobResponse(
            job_id=job_id,
            status="completed",
            summary=job.summary,
        )
    
    # Build extension_extracted from existing job fields
    extension_extracted = {
        "job_url": job.job_url,
        "job_title": job.job_title,
        "company_name": job.company_name,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary_raw": job.salary_raw,
        "seniority": job.seniority,
        "remote_type": job.remote_type,
        "role_type": job.role_type,
        "location": job.location,
        "required_skills": job.required_skills,
        "source": job.source,
    }
    
    # Get settings for DB URL
    settings = Settings()
    
    # Start background analysis
    background_tasks.add_task(
        run_analysis_background,
        job_id=str(job.id),
        job_url=job.job_url,
        raw_text=job.scraped_text_debug or "",
        extension_extracted=extension_extracted,
        db_url=settings.database_url,
    )
    
    logger.info(f"Started job analysis for {job_id}")
    
    return AnalyzeJobResponse(
        job_id=job_id,
        status="started",
    )


@router.get("/{job_id}", response_model=AnalyzeJobResponse)
async def get_analysis_status(
    job_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get the analysis status/results for a job.
    """
    # Validate job_id
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    # Check if user has access (try saved_job.id first, then job.id)
    saved_job = db.query(SavedJob).filter(
        SavedJob.id == job_uuid,
        SavedJob.user_id == user_id,
    ).first()
    
    if not saved_job:
        saved_job = db.query(SavedJob).filter(
            SavedJob.job_id == job_uuid,
            SavedJob.user_id == user_id,
        ).first()
    
    if not saved_job:
        raise HTTPException(status_code=404, detail="Job not found or not saved by user")
    
    # Get the job via relationship
    job = saved_job.job
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check analysis status
    if job.summary:
        return AnalyzeJobResponse(
            job_id=job_id,
            status="completed",
            summary=job.summary,
        )
    else:
        return AnalyzeJobResponse(
            job_id=job_id,
            status="pending",
        )


class CheckpointInfo(BaseModel):
    """Information about a checkpoint."""
    checkpoint_id: str
    thread_id: str
    checkpoint_ns: str
    parent_checkpoint_id: Optional[str] = None


class AnalysisHistoryResponse(BaseModel):
    """Response containing analysis checkpoint history."""
    job_id: str
    checkpoint_count: int
    checkpoints: List[dict]


@router.get("/{job_id}/history", response_model=AnalysisHistoryResponse)
async def get_analysis_history(
    job_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get the checkpoint history (audit trail) for a job analysis.
    
    Returns all intermediate states captured during the LangGraph pipeline execution.
    Each checkpoint includes:
    - The node that was executed
    - The state at that point
    - Timestamp information
    """
    from ..graphs import get_job_intake_history
    
    # Validate job_id
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    # Check if user has access
    saved_job = db.query(SavedJob).filter(
        SavedJob.id == job_uuid,
        SavedJob.user_id == user_id,
    ).first()
    
    if not saved_job:
        saved_job = db.query(SavedJob).filter(
            SavedJob.job_id == job_uuid,
            SavedJob.user_id == user_id,
        ).first()
    
    if not saved_job:
        raise HTTPException(status_code=404, detail="Job not found or not saved by user")
    
    job = saved_job.job
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get checkpoint history
    checkpoints = get_job_intake_history(str(job.id))
    
    # Format checkpoints for response
    formatted_checkpoints = []
    for checkpoint in checkpoints:
        # Extract key info from checkpoint tuple
        try:
            # Get metadata which contains the node that was executed
            metadata = checkpoint.metadata if hasattr(checkpoint, "metadata") else {}
            
            # Get the actual state from the checkpoint
            # checkpoint.checkpoint contains the serialized state with channel_values
            state_data = {}
            if hasattr(checkpoint, "checkpoint") and checkpoint.checkpoint:
                channel_values = checkpoint.checkpoint.get("channel_values", {})
                
                # Get jobdoc values (the extracted job fields)
                jobdoc = channel_values.get("jobdoc", {}) or {}
                
                # Get segments (text sections)
                segments = channel_values.get("segments", {}) or {}
                # Truncate segment values to avoid huge responses
                segments_preview = {k: (v[:200] + "..." if len(v) > 200 else v) for k, v in segments.items()} if segments else {}
                
                # Extract key state fields (avoid huge raw_text dumps)
                state_data = {
                    "current_node": channel_values.get("current_node"),
                    "job_id": channel_values.get("job_id"),
                    "errors": channel_values.get("errors", []),
                    "persisted": channel_values.get("persisted"),
                    "has_summary": bool(channel_values.get("job_summary")),
                    "summary_preview": (channel_values.get("job_summary") or "")[:500] + "..." if channel_values.get("job_summary") else None,
                    "jobdoc": jobdoc,  # Full extracted job document
                    "segments": segments_preview,  # Truncated text segments
                    "extraction_evidence": channel_values.get("extraction_evidence", []),
                }
            
            checkpoint_data = {
                "checkpoint_id": checkpoint.config.get("configurable", {}).get("checkpoint_id", ""),
                "thread_id": checkpoint.config.get("configurable", {}).get("thread_id", ""),
                "parent_id": checkpoint.parent_config.get("configurable", {}).get("checkpoint_id") if checkpoint.parent_config else None,
                "step": metadata.get("step"),
                "node": metadata.get("source"),  # Which node produced this checkpoint
                "writes": metadata.get("writes"),  # What was written
                "state": state_data,
            }
            formatted_checkpoints.append(checkpoint_data)
        except Exception as e:
            logger.warning(f"Failed to format checkpoint: {e}")
            # Include raw checkpoint if formatting fails
            formatted_checkpoints.append({"raw": str(checkpoint), "error": str(e)})
    
    return AnalysisHistoryResponse(
        job_id=job_id,
        checkpoint_count=len(formatted_checkpoints),
        checkpoints=formatted_checkpoints,
    )
