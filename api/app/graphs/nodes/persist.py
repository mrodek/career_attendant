"""
Node 6: persist_job_artifacts

Saves the extracted and generated data to the database and ChromaDB.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ..state import JobIntakeState


def persist_job_artifacts(
    state: JobIntakeState,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Persist job artifacts to the database and ChromaDB.
    
    This node:
    1. Updates the Job record with LLM-extracted fields
    2. Saves the job summary
    3. Creates embeddings in ChromaDB for semantic search
    
    Inputs:
        - job_id: UUID of the job record
        - jobdoc: Merged JobDoc with all extracted fields
        - job_summary: Generated summary
        - db: SQLAlchemy session (passed as context)
    
    Outputs:
        - persisted: Whether persistence succeeded
        - embedding_id: ChromaDB document ID
        - current_node: Updated tracker
    """
    errors = list(state.get("errors", []))
    job_id = state.get("job_id")
    jobdoc = state.get("jobdoc", {})
    job_summary = state.get("job_summary", "")
    
    persisted = False
    embedding_id = None
    
    # === 1. Update Job in PostgreSQL ===
    if db and job_id:
        try:
            from ...models import Job
            
            job = db.query(Job).filter(Job.id == job_id).first()
            
            if job:
                # Update with LLM-extracted fields
                # jobdoc contains the merged best values from extension + LLM extraction
                # Always update if jobdoc has a value (LLM validation may have corrected garbage)
                
                # Core job info - always update from jobdoc if available
                if jobdoc.get("job_title"):
                    job.job_title = jobdoc["job_title"]
                if jobdoc.get("company_name"):
                    job.company_name = jobdoc["company_name"]
                if jobdoc.get("location"):
                    job.location = jobdoc["location"]
                
                # Salary
                if jobdoc.get("salary_min"):
                    job.salary_min = jobdoc["salary_min"]
                if jobdoc.get("salary_max"):
                    job.salary_max = jobdoc["salary_max"]
                if jobdoc.get("salary_currency"):
                    job.salary_currency = jobdoc["salary_currency"]
                if jobdoc.get("salary_period"):
                    job.salary_period = jobdoc["salary_period"]
                
                # Posting date
                if jobdoc.get("posting_date"):
                    from datetime import date
                    pd = jobdoc["posting_date"]
                    if isinstance(pd, str):
                        try:
                            job.posting_date = date.fromisoformat(pd)
                        except ValueError:
                            pass  # Invalid date format, skip
                    elif isinstance(pd, date):
                        job.posting_date = pd
                
                # Experience & seniority
                if jobdoc.get("seniority"):
                    job.seniority = jobdoc["seniority"]
                if jobdoc.get("years_experience_min"):
                    job.years_experience_min = jobdoc["years_experience_min"]
                if jobdoc.get("years_experience_max"):
                    job.years_experience_max = jobdoc["years_experience_max"]
                
                # Skills
                if jobdoc.get("required_skills"):
                    job.required_skills = jobdoc["required_skills"]
                if jobdoc.get("preferred_skills"):
                    job.preferred_skills = jobdoc["preferred_skills"]
                
                # Work arrangement
                if jobdoc.get("remote_type"):
                    job.remote_type = jobdoc["remote_type"]
                if jobdoc.get("role_type"):
                    job.role_type = jobdoc["role_type"]
                
                # Industry
                if jobdoc.get("industry"):
                    job.industry = jobdoc["industry"]
                
                # Save summary
                if job_summary:
                    job.summary = job_summary
                    job.summary_generated_at = datetime.now(timezone.utc)
                
                db.flush()
                persisted = True
            else:
                errors.append(f"Job {job_id} not found in database")
                
        except Exception as e:
            errors.append(f"Database update failed: {str(e)}")
    
    # === 2. Create Embeddings in ChromaDB ===
    if job_summary and job_id:
        try:
            from ..config import get_config
            
            config = get_config()
            collection = config.get_job_collection()
            
            # Create document for embedding
            doc_text = f"""
Job Title: {jobdoc.get('job_title', '')}
Company: {jobdoc.get('company_name', '')}
Location: {jobdoc.get('location', '')}
Skills: {', '.join(jobdoc.get('required_skills', []))}

Summary:
{job_summary}
"""
            
            embedding_id = f"job_{job_id}"
            
            # Upsert to ChromaDB
            collection.upsert(
                ids=[embedding_id],
                documents=[doc_text],
                metadatas=[{
                    "job_id": str(job_id),
                    "job_title": jobdoc.get("job_title", ""),
                    "company_name": jobdoc.get("company_name", ""),
                    "seniority": jobdoc.get("seniority", ""),
                }]
            )
            
            # Update job with embedding ID
            if db and job_id:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    job.embedding_id = embedding_id
                    db.flush()
                    
        except Exception as e:
            errors.append(f"ChromaDB embedding failed: {str(e)}")
            # Non-fatal - continue even if embeddings fail
    
    return {
        "persisted": persisted,
        "embedding_id": embedding_id,
        "current_node": "persist_job_artifacts",
        "errors": errors,
    }


def persist_job_artifacts_with_db(db: Session):
    """
    Factory function to create a persist node with database context.
    
    Usage in graph:
        graph.add_node("persist", persist_job_artifacts_with_db(db))
    """
    def _persist(state: JobIntakeState) -> Dict[str, Any]:
        return persist_job_artifacts(state, db=db)
    return _persist
