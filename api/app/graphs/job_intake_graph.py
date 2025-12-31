"""
Job Intake & Analysis Graph

This is the main LangGraph definition that orchestrates the job intake pipeline.
Triggered when a job is saved via the extension.

Flow:
1. ingest_raw_capture - Validate and prepare input
2. preprocess_and_segment - Clean and segment text (deterministic)
3. extract_structured_fields - LLM extraction/validation
4. generate_job_summary - LLM summary generation
5. persist_job_artifacts - Save to DB and ChromaDB

Checkpointing:
- State is persisted after each node via PostgresSaver
- Enables audit trail, resume capability, and time-travel debugging
"""

import os
import logging
from typing import Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy.orm import Session
from psycopg import Connection
from psycopg.rows import dict_row

from .state import JobIntakeState
from .nodes import (
    ingest_raw_capture,
    preprocess_and_segment,
    extract_structured_fields,
    generate_job_summary,
)
from .nodes.persist import persist_job_artifacts_with_db

logger = logging.getLogger("api")

# Global checkpointer and connection (initialized once)
_checkpointer: Optional[PostgresSaver] = None
_db_connection: Optional[Connection] = None


def get_checkpointer() -> Optional[PostgresSaver]:
    """
    Get or create the PostgreSQL checkpointer for state persistence.
    
    Returns None if database URL is not configured.
    """
    global _checkpointer, _db_connection
    
    if _checkpointer is not None:
        return _checkpointer
    
    # Get database URL and convert for psycopg3
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        logger.warning("DATABASE_URL not set, checkpointing disabled")
        return None
    
    # Convert SQLAlchemy URL to psycopg format
    # postgresql+psycopg://user:pass@host:port/db -> postgresql://user:pass@host:port/db
    psycopg_url = db_url.replace("postgresql+psycopg://", "postgresql://")
    
    try:
        # Create connection with autocommit=True (required for setup() which uses CONCURRENTLY)
        _db_connection = Connection.connect(
            psycopg_url,
            autocommit=True,
            prepare_threshold=0,
            row_factory=dict_row
        )
        
        # Create checkpointer with the connection
        _checkpointer = PostgresSaver(conn=_db_connection)
        
        # Setup creates tables if they don't exist
        _checkpointer.setup()
        logger.info("LangGraph checkpointer initialized successfully")
        
        return _checkpointer
    except Exception as e:
        logger.error(f"Failed to initialize checkpointer: {e}")
        return None


def should_continue_after_ingest(state: JobIntakeState) -> str:
    """Determine if we should continue after ingestion."""
    errors = state.get("errors", [])
    if errors:
        return "end"
    return "preprocess"


def should_continue_after_preprocess(state: JobIntakeState) -> str:
    """Determine if we should continue after preprocessing."""
    doc_stats = state.get("doc_stats", {})
    # Skip LLM if very short content
    if doc_stats.get("char_count", 0) < 100:
        return "end"
    return "extract"


def should_run_summary(state: JobIntakeState) -> str:
    """Determine if we should generate a summary."""
    jobdoc = state.get("jobdoc", {})
    # Only summarize if we have meaningful extracted data
    if jobdoc.get("job_title") or jobdoc.get("required_skills"):
        return "summarize"
    return "persist"


def create_job_intake_graph(db: Optional[Session] = None, use_checkpointer: bool = True):
    """
    Create the job intake graph with optional database context and checkpointing.
    
    Args:
        db: SQLAlchemy session for persistence (optional for testing)
        use_checkpointer: Whether to enable state checkpointing (default True)
    
    Returns:
        Compiled StateGraph ready to invoke
    """
    # Create the graph
    workflow = StateGraph(JobIntakeState)
    
    # === Add Nodes ===
    workflow.add_node("ingest", ingest_raw_capture)
    workflow.add_node("preprocess", preprocess_and_segment)
    workflow.add_node("extract", extract_structured_fields)
    workflow.add_node("summarize", generate_job_summary)
    
    # Persist node needs DB context
    if db:
        workflow.add_node("persist", persist_job_artifacts_with_db(db))
    else:
        # Stub for testing without DB
        workflow.add_node("persist", lambda state: {
            "persisted": False,
            "current_node": "persist",
            "errors": state.get("errors", []) + ["No database connection"],
        })
    
    # === Set Entry Point ===
    workflow.set_entry_point("ingest")
    
    # === Add Edges ===
    # Conditional edge after ingest
    workflow.add_conditional_edges(
        "ingest",
        should_continue_after_ingest,
        {
            "preprocess": "preprocess",
            "end": END,
        }
    )
    
    # Conditional edge after preprocess
    workflow.add_conditional_edges(
        "preprocess",
        should_continue_after_preprocess,
        {
            "extract": "extract",
            "end": END,
        }
    )
    
    # Conditional edge after extract
    workflow.add_conditional_edges(
        "extract",
        should_run_summary,
        {
            "summarize": "summarize",
            "persist": "persist",
        }
    )
    
    # Linear edges
    workflow.add_edge("summarize", "persist")
    workflow.add_edge("persist", END)
    
    # Compile with or without checkpointer
    checkpointer = get_checkpointer() if use_checkpointer else None
    if checkpointer:
        logger.info("Compiling graph with PostgreSQL checkpointer")
        return workflow.compile(checkpointer=checkpointer)
    else:
        logger.info("Compiling graph without checkpointer")
        return workflow.compile()


async def run_job_intake(
    job_id: str,
    job_url: str,
    raw_text: str,
    extension_extracted: Dict[str, Any],
    db: Optional[Session] = None,
) -> JobIntakeState:
    """
    Run the job intake pipeline for a saved job.
    
    Args:
        job_id: UUID of the job record in the database
        job_url: URL of the job posting
        raw_text: Scraped text from the extension (scraped_text_debug)
        extension_extracted: Fields already extracted by the extension
        db: SQLAlchemy session for persistence
    
    Returns:
        Final state with all extracted and generated data
    """
    # Create the graph
    graph = create_job_intake_graph(db)
    
    # Build initial state
    initial_state: JobIntakeState = {
        "job_id": job_id,
        "job_url": job_url,
        "raw_text": raw_text,
        "extension_extracted": extension_extracted,
        "errors": [],
    }
    
    # Config with thread_id for checkpoint tracking
    # Using job_id as thread_id allows retrieving history by job
    config = {"configurable": {"thread_id": job_id}}
    
    # Run the graph with checkpoint tracking
    final_state = await graph.ainvoke(initial_state, config)
    
    return final_state


def run_job_intake_sync(
    job_id: str,
    job_url: str,
    raw_text: str,
    extension_extracted: Dict[str, Any],
    db: Optional[Session] = None,
) -> JobIntakeState:
    """
    Synchronous version of run_job_intake.
    
    Use this when calling from non-async contexts.
    """
    graph = create_job_intake_graph(db)
    
    initial_state: JobIntakeState = {
        "job_id": job_id,
        "job_url": job_url,
        "raw_text": raw_text,
        "extension_extracted": extension_extracted,
        "errors": [],
    }
    
    # Config with thread_id for checkpoint tracking
    config = {"configurable": {"thread_id": job_id}}
    
    final_state = graph.invoke(initial_state, config)
    
    return final_state


def get_job_intake_history(job_id: str) -> list:
    """
    Retrieve checkpoint history for a job analysis.
    
    Args:
        job_id: UUID of the job to retrieve history for
    
    Returns:
        List of checkpoint states in chronological order
    """
    checkpointer = get_checkpointer()
    if not checkpointer:
        return []
    
    config = {"configurable": {"thread_id": job_id}}
    
    try:
        # List all checkpoints for this thread
        checkpoints = list(checkpointer.list(config))
        return checkpoints
    except Exception as e:
        logger.error(f"Failed to retrieve checkpoint history: {e}")
        return []
