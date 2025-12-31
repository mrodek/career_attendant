"""
Node 3: extract_structured_fields

Uses LLM to extract/validate structured fields from the job description.
This augments what the extension already extracted, filling gaps and validating.
"""

import json
from typing import Any, Dict, List, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser

from ..state import JobIntakeState, JobDocPartial
from ..config import get_llm


EXTRACTION_SYSTEM_PROMPT = """You are a job posting analyzer. Extract structured information from job descriptions.

Your task is to extract ONLY the information that is explicitly stated or clearly implied in the text.
DO NOT hallucinate or infer information that isn't there.

For each field you extract, provide:
1. The extracted value
2. A short quote from the text as evidence (max 50 chars)
3. Confidence level: "high", "medium", or "low"

Return a JSON object with this structure:
{
    "extractions": {
        "field_name": {
            "value": <extracted value>,
            "evidence": "<quote from text>",
            "confidence": "high|medium|low"
        }
    },
    "fields_not_found": ["field1", "field2"]
}

Fields to extract:
- job_title: The job title/position name
- company_name: The hiring company name
- seniority: One of: intern, junior, mid, senior, staff, principal, director, vp, cxo
- years_experience_min: Minimum years of experience required (integer)
- years_experience_max: Maximum years of experience (integer, if range given)
- salary_min: Minimum salary (integer, annual USD)
- salary_max: Maximum salary (integer, annual USD)
- salary_period: One of: year, month, hour
- remote_type: One of: remote, hybrid, onsite
- role_type: One of: full_time, part_time, contract
- location: Primary work location
- required_skills: Array of required technical skills (max 15)
- preferred_skills: Array of nice-to-have skills (max 10)

IMPORTANT:
- Only extract what you can find evidence for
- For skills, only include specific technical skills, not soft skills
- For salary, convert to annual USD if given in other formats
- If a field is already provided and looks correct, you can skip re-extracting it
"""


def merge_extractions(
    extension_extracted: JobDocPartial,
    llm_extracted: Dict[str, Any],
) -> JobDocPartial:
    """
    Merge extension-extracted fields with LLM-extracted fields.
    
    Priority:
    1. Extension values are kept if they exist and LLM confidence is not "high"
    2. LLM values override if extension value is missing or LLM confidence is "high"
    """
    merged: JobDocPartial = dict(extension_extracted)
    extractions = llm_extracted.get("extractions", {})
    
    for field_name, extraction in extractions.items():
        value = extraction.get("value")
        confidence = extraction.get("confidence", "low")
        
        if value is None:
            continue
            
        # Check if extension already has this field
        existing = merged.get(field_name)
        
        # Override if: no existing value OR high confidence from LLM
        if existing is None or confidence == "high":
            merged[field_name] = value
    
    return merged


def build_extraction_evidence(llm_extracted: Dict[str, Any]) -> List[dict]:
    """Build evidence list from LLM extractions."""
    evidence = []
    extractions = llm_extracted.get("extractions", {})
    
    for field_name, extraction in extractions.items():
        if extraction.get("value") is not None:
            evidence.append({
                "field": field_name,
                "value": extraction.get("value"),
                "evidence": extraction.get("evidence", ""),
                "confidence": extraction.get("confidence", "low"),
                "source": "llm",
            })
    
    return evidence


def extract_structured_fields(state: JobIntakeState) -> Dict[str, Any]:
    """
    Use LLM to extract/validate structured fields from job text.
    
    This node:
    1. Takes the segmented text and extension-extracted fields
    2. Asks LLM to extract missing fields and validate existing ones
    3. Merges results, preferring high-confidence LLM extractions
    
    Inputs:
        - segmented: Segmented text sections
        - extension_extracted: Fields already extracted by extension
    
    Outputs:
        - llm_extracted: Raw LLM extraction results
        - extraction_evidence: Evidence for each extraction
        - jobdoc: Merged JobDoc (extension + LLM)
        - current_node: Updated tracker
    """
    errors = list(state.get("errors", []))
    segmented = state.get("segmented", {})
    extension_extracted = state.get("extension_extracted", {})
    
    # Get the best text to analyze
    text_to_analyze = (
        segmented.get("requirements", "") + "\n\n" +
        segmented.get("responsibilities", "") + "\n\n" +
        segmented.get("about", "") + "\n\n" +
        segmented.get("full_text", "")[:5000]  # Limit context
    )
    
    if not text_to_analyze.strip():
        errors.append("No text available for LLM extraction")
        return {
            "llm_extracted": {},
            "extraction_evidence": [],
            "jobdoc": extension_extracted,
            "current_node": "extract_structured_fields",
            "errors": errors,
        }
    
    # Build prompt with context about what's already extracted
    already_extracted = {k: v for k, v in extension_extracted.items() if v is not None}
    
    human_message = f"""Analyze this job posting and extract structured fields.

Already extracted by client (validate these):
{json.dumps(already_extracted, indent=2)}

Job posting text:
---
{text_to_analyze[:8000]}
---

Extract any missing fields and validate the existing ones. Return JSON only."""

    try:
        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(content=human_message),
        ])
        
        # Parse JSON response
        response_text = response.content
        
        # Try to extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        llm_extracted = json.loads(response_text.strip())
        
    except json.JSONDecodeError as e:
        errors.append(f"Failed to parse LLM response as JSON: {str(e)}")
        llm_extracted = {}
    except Exception as e:
        errors.append(f"LLM extraction failed: {str(e)}")
        llm_extracted = {}
    
    # Merge extractions
    jobdoc = merge_extractions(extension_extracted, llm_extracted)
    
    # Build evidence
    extraction_evidence = build_extraction_evidence(llm_extracted)
    
    # Add extension-extracted fields to evidence
    for field, value in extension_extracted.items():
        if value is not None:
            extraction_evidence.append({
                "field": field,
                "value": value,
                "evidence": "Client-side extraction",
                "confidence": "medium",
                "source": "extension",
            })
    
    return {
        "llm_extracted": llm_extracted,
        "extraction_evidence": extraction_evidence,
        "jobdoc": jobdoc,
        "current_node": "extract_structured_fields",
        "errors": errors,
    }
