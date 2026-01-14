"""
Streaming extraction endpoint for real-time job analysis.

Uses Server-Sent Events (SSE) to stream extraction progress to the client.
"""

import json
import logging
from typing import Optional, List, AsyncGenerator
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..graphs.state import JobIntakeState, JobDocPartial

logger = logging.getLogger("api")

router = APIRouter(prefix="/extract", tags=["extraction"])


class ExtractRequest(BaseModel):
    """Request body for extraction endpoint."""
    job_url: str
    raw_text: str
    extension_extracted: Optional[dict] = Field(default_factory=dict)


class FieldConfidence(BaseModel):
    """Confidence info for an extracted field."""
    value: Optional[str | int | list] = None
    confidence: str = "low"  # high, medium, low
    source: str = "unknown"  # extension, llm


class ExtractionProgress(BaseModel):
    """Progress update during extraction."""
    node: str
    status: str  # started, complete, error
    progress: int  # 0-100
    message: Optional[str] = None
    # Partial results
    fields: Optional[dict] = None
    confidence: Optional[dict] = None
    segments: Optional[dict] = None
    summary: Optional[str] = None
    error: Optional[str] = None


def format_sse(data: dict) -> str:
    """Format data as Server-Sent Event."""
    return f"data: {json.dumps(data)}\n\n"


async def run_extraction_stream(
    job_url: str,
    raw_text: str,
    extension_extracted: dict,
) -> AsyncGenerator[str, None]:
    """
    Run extraction pipeline and yield SSE events after each node.
    """
    from ..graphs.nodes import (
        ingest_raw_capture,
        preprocess_and_segment,
        extract_structured_fields,
        generate_job_summary,
    )
    
    # Build initial state
    state: JobIntakeState = {
        "job_id": "",  # No job_id yet - extraction only
        "job_url": job_url,
        "raw_text": raw_text,
        "extension_extracted": extension_extracted or {},
        "errors": [],
    }
    
    nodes = [
        ("ingest", ingest_raw_capture, 20),
        ("preprocess", preprocess_and_segment, 40),
        ("extract", extract_structured_fields, 70),
        ("summarize", generate_job_summary, 100),
    ]
    
    try:
        for node_name, node_func, progress in nodes:
            # Send "started" event
            yield format_sse({
                "node": node_name,
                "status": "started",
                "progress": progress - 15,
                "message": f"Running {node_name}...",
            })
            
            try:
                # Run node (some are sync, wrap if needed)
                result = node_func(state)
                
                # Merge result into state
                state.update(result)
                
                # Build response based on node
                event_data = {
                    "node": node_name,
                    "status": "complete",
                    "progress": progress,
                }
                
                if node_name == "preprocess":
                    event_data["segments"] = state.get("segmented", {})
                    event_data["message"] = f"Found {state.get('doc_stats', {}).get('word_count', 0)} words"
                
                elif node_name == "extract":
                    # Include extracted fields with confidence
                    jobdoc = state.get("jobdoc", {})
                    evidence = state.get("extraction_evidence", [])
                    comprehensive = state.get("comprehensive_analysis", {})
                    
                    logger.info(f"Extract node complete. comprehensive_analysis keys: {list(comprehensive.keys()) if comprehensive else 'EMPTY'}")
                    
                    # Build confidence map
                    confidence_map = {}
                    for ev in evidence:
                        field = ev.get("field")
                        if field:
                            confidence_map[field] = {
                                "confidence": ev.get("confidence", "low"),
                                "source": ev.get("source", "unknown"),
                            }
                    
                    event_data["fields"] = jobdoc
                    event_data["confidence"] = confidence_map
                    event_data["comprehensive_analysis"] = comprehensive
                    event_data["message"] = f"Extracted {len(jobdoc)} fields"
                
                elif node_name == "summarize":
                    event_data["summary"] = state.get("job_summary", "")
                    event_data["message"] = "Summary generated"
                
                yield format_sse(event_data)
                
            except Exception as e:
                logger.error(f"Error in node {node_name}: {e}")
                yield format_sse({
                    "node": node_name,
                    "status": "error",
                    "progress": progress,
                    "error": str(e),
                    "message": f"Error in {node_name}: {str(e)[:100]}",
                })
                # Continue to next node or stop based on severity
                if node_name in ["ingest", "preprocess"]:
                    # Critical nodes - stop pipeline
                    yield format_sse({
                        "status": "failed",
                        "error": str(e),
                        "message": "Extraction failed - please retry",
                    })
                    return
        
        # Final success event
        yield format_sse({
            "status": "done",
            "progress": 100,
            "message": "Extraction complete",
            "fields": state.get("jobdoc", {}),
            "summary": state.get("job_summary", ""),
        })
        
    except Exception as e:
        logger.error(f"Extraction stream error: {e}")
        yield format_sse({
            "status": "failed",
            "error": str(e),
            "message": "Extraction failed unexpectedly",
        })


@router.post("/stream")
async def extract_stream(request: ExtractRequest):
    """
    Stream job extraction progress via Server-Sent Events.
    
    Returns real-time updates as the extraction pipeline processes the job posting:
    - ingest: Validates and prepares raw text
    - preprocess: Segments text into sections
    - extract: LLM extracts structured fields
    - summarize: Generates job summary
    
    Each event contains:
    - node: Current processing node
    - status: started | complete | error
    - progress: 0-100 percentage
    - fields: Extracted fields (after extract node)
    - confidence: Confidence scores per field
    - summary: Job summary (after summarize node)
    """
    logger.info(f"Extract stream called for URL: {request.job_url}")
    if not request.raw_text or len(request.raw_text) < 100:
        raise HTTPException(
            status_code=400,
            detail="raw_text must be at least 100 characters"
        )
    
    return StreamingResponse(
        run_extraction_stream(
            job_url=request.job_url,
            raw_text=request.raw_text,
            extension_extracted=request.extension_extracted or {},
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post("/")
async def extract_sync(request: ExtractRequest):
    """
    Synchronous extraction endpoint (non-streaming fallback).
    
    Returns all extraction results at once after pipeline completes.
    """
    from ..graphs.nodes import (
        ingest_raw_capture,
        preprocess_and_segment,
        extract_structured_fields,
        generate_job_summary,
    )
    
    if not request.raw_text or len(request.raw_text) < 100:
        raise HTTPException(
            status_code=400,
            detail="raw_text must be at least 100 characters"
        )
    
    # Build initial state
    state: JobIntakeState = {
        "job_id": "",
        "job_url": request.job_url,
        "raw_text": request.raw_text,
        "extension_extracted": request.extension_extracted or {},
        "errors": [],
    }
    
    try:
        # Run pipeline
        state.update(ingest_raw_capture(state))
        state.update(preprocess_and_segment(state))
        state.update(extract_structured_fields(state))
        state.update(generate_job_summary(state))
        
        # Build confidence map
        evidence = state.get("extraction_evidence", [])
        confidence_map = {}
        for ev in evidence:
            field = ev.get("field")
            if field:
                confidence_map[field] = {
                    "confidence": ev.get("confidence", "low"),
                    "source": ev.get("source", "unknown"),
                }
        
        return {
            "status": "success",
            "fields": state.get("jobdoc", {}),
            "confidence": confidence_map,
            "summary": state.get("job_summary", ""),
            "errors": state.get("errors", []),
        }
        
    except Exception as e:
        logger.error(f"Sync extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
