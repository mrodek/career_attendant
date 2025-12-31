"""
Node 1: ingest_raw_capture

Validates the incoming payload and prepares it for processing.
This bridges the extension's extracted data with the LangGraph pipeline.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from ..state import JobIntakeState, JobDocPartial


def ingest_raw_capture(state: JobIntakeState) -> Dict[str, Any]:
    """
    Validate and ingest the raw job capture from the extension.
    
    Inputs (from state):
        - job_id: UUID of the job record
        - job_url: URL of the job posting
        - raw_text: Scraped text (scraped_text_debug)
        - extension_extracted: Fields already extracted by the extension
    
    Outputs:
        - thread_id: Unique ID for this analysis run
        - ingested_at: Timestamp
        - current_node: Updated node tracker
        - errors: Any validation errors
    """
    errors = list(state.get("errors", []))
    
    # Validate required fields
    if not state.get("job_url"):
        errors.append("job_url is required")
    
    if not state.get("raw_text") and not state.get("extension_extracted"):
        errors.append("Either raw_text or extension_extracted is required")
    
    # Generate thread ID for this analysis run
    thread_id = str(uuid.uuid4())
    
    # Normalize extension_extracted to ensure it's a proper dict
    extension_extracted = state.get("extension_extracted", {})
    if not isinstance(extension_extracted, dict):
        extension_extracted = {}
    
    return {
        "thread_id": thread_id,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "extension_extracted": extension_extracted,
        "current_node": "ingest_raw_capture",
        "errors": errors,
    }
