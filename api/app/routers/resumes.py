from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging

from .. import crud, models, schemas
from ..db import get_db
from ..storage import save_file, delete_file
from ..production_storage import get_storage_backend
from ..auth.dependencies import get_current_user
from ..config import Settings
from ..graphs.resume_graph import run_resume_processing_sync

logger = logging.getLogger("api")

router = APIRouter(
    prefix="/resumes",
    tags=["resumes"],
)


def process_resume_background(
    resume_id: str,
    user_id: str,
    file_path: str,
    file_type: str,
    db_url: str,
):
    """Background task to process a resume."""
    try:
        logger.info(f"Starting background resume processing for {resume_id}")
        result = run_resume_processing_sync(
            resume_id=resume_id,
            user_id=user_id,
            file_path=file_path,
            file_type=file_type,
            db_url=db_url,
        )
        logger.info(f"Background resume processing completed: {result.get('processing_status')}")
    except Exception as e:
        logger.error(f"Background resume processing failed: {e}")
        # Update status to failed
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        try:
            resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
            if resume:
                resume.processing_status = "failed"
                resume.error_message = str(e)
                db.commit()
        finally:
            db.close()


@router.post("/", response_model=schemas.ResumeOut)
async def create_resume(
    background_tasks: BackgroundTasks,
    resume_name: str = Form(...),
    is_primary: bool = Form(False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Upload a new resume."""
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF and DOCX are allowed."
        )
    
    # Save the file using production-ready storage
    storage_backend = get_storage_backend()
    file_path = await storage_backend.save_file(file, user.id)

    # Create the resume record in the database
    resume = crud.create_resume(
        db=db,
        user_id=user.id,
        resume_name=resume_name,
        file_name=file.filename,
        file_path=file_path,
        file_size=file.size or 0,
        file_type=file.content_type,
        is_primary=is_primary,
    )

    # Start the processing pipeline in the background
    settings = Settings()
    background_tasks.add_task(
        process_resume_background,
        resume_id=str(resume.id),
        user_id=user.id,
        file_path=file_path,
        file_type=file.content_type,
        db_url=settings.database_url,
    )
    logger.info(f"Resume {resume.id} created, background processing started")

    return resume


@router.get("/", response_model=List[schemas.ResumeOutWithDecrypted])
async def list_resumes(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """List all resumes for the current user with decrypted data."""
    resumes = db.query(models.Resume).filter(
        models.Resume.user_id == user.id
    ).order_by(models.Resume.created_at.desc()).all()
    
    # Return decrypted data
    return [schemas.ResumeOutWithDecrypted.from_resume(resume) for resume in resumes]


@router.get("/{resume_id}", response_model=schemas.ResumeOutWithDecrypted)
async def get_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Get a specific resume by ID with decrypted data."""
    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id,
        models.Resume.user_id == user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return schemas.ResumeOutWithDecrypted.from_resume(resume)


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Delete a resume."""
    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id,
        models.Resume.user_id == user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Delete the file from storage
    await delete_file(resume.file_path)
    
    # Delete from database
    db.delete(resume)
    db.commit()
    
    return {"message": "Resume deleted successfully"}


@router.patch("/{resume_id}", response_model=schemas.ResumeOut)
async def update_resume(
    resume_id: UUID,
    updates: schemas.ResumeUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Update resume metadata."""
    resume = db.query(models.Resume).filter(
        models.Resume.id == resume_id,
        models.Resume.user_id == user.id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Update fields
    if updates.resume_name is not None:
        resume.resume_name = updates.resume_name
    
    if updates.is_primary is not None:
        # If setting as primary, unset all other primaries
        if updates.is_primary:
            db.query(models.Resume).filter(
                models.Resume.user_id == user.id,
                models.Resume.id != resume_id
            ).update({"is_primary": False})
        resume.is_primary = updates.is_primary
    
    db.commit()
    db.refresh(resume)
    
    return resume
