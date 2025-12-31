"""
Configuration for LangGraph pipelines.

Handles LLM clients, ChromaDB setup, and environment variables.
"""

import os
from functools import lru_cache
from typing import Optional

from langchain_openai import ChatOpenAI
import chromadb
from chromadb.config import Settings as ChromaSettings

from .llm_logger import get_llm_callbacks


class GraphConfig:
    """Configuration for the job intake graph."""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        
        # Validation
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
    
    @property
    def llm(self) -> ChatOpenAI:
        """Get the configured LLM client with logging callbacks."""
        return ChatOpenAI(
            model=self.openai_model,
            temperature=0.1,  # Low temperature for consistent extraction
            api_key=self.openai_api_key,
            callbacks=get_llm_callbacks(),
        )
    
    @property
    def llm_creative(self) -> ChatOpenAI:
        """Get LLM client for creative tasks (summaries) with logging callbacks."""
        return ChatOpenAI(
            model=self.openai_model,
            temperature=0.7,
            api_key=self.openai_api_key,
            callbacks=get_llm_callbacks(),
        )
    
    @property
    def chroma_client(self) -> chromadb.ClientAPI:
        """Get ChromaDB client for embeddings."""
        return chromadb.Client(ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=self.chroma_persist_dir,
            anonymized_telemetry=False,
        ))
    
    def get_job_collection(self):
        """Get or create the jobs collection in ChromaDB."""
        return self.chroma_client.get_or_create_collection(
            name="job_documents",
            metadata={"description": "Job descriptions and summaries for semantic search"}
        )


@lru_cache()
def get_config() -> GraphConfig:
    """Get cached graph configuration."""
    return GraphConfig()


def get_llm() -> ChatOpenAI:
    """Convenience function to get the default LLM."""
    return get_config().llm


def get_llm_creative() -> ChatOpenAI:
    """Convenience function to get the creative LLM."""
    return get_config().llm_creative
