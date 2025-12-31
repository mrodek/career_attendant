"""
Node 3: extract_structured_fields

Uses LLM to extract/validate structured fields from the job description.
This augments what the extension already extracted, filling gaps and validating.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser

from ..state import JobIntakeState, JobDocPartial
from ..config import get_llm

logger = logging.getLogger("api")


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
- industry: The company's industry (e.g., "Enterprise Software", "Healthcare", "Finance", "E-commerce", "AI/ML")
- seniority: One of: intern, junior, mid, senior, staff, principal, director, vp, cxo
- years_experience_min: Minimum years of experience required (integer)
- years_experience_max: Maximum years of experience (integer, if range given)
- salary_min: Minimum salary (integer, annual)
- salary_max: Maximum salary (integer, annual)
- salary_currency: Currency code (e.g., "USD", "GBP", "EUR", "CAD"). Infer from $ (USD), £ (GBP), € (EUR), or country context.
- salary_period: One of: year, month, hour
- posting_date: When the job was posted (ISO format YYYY-MM-DD). Look for "Posted X days ago", "Posted on [date]", etc.
- remote_type: One of: remote, hybrid, onsite (look for "remote", "work from home", "hybrid", "in-office", "on-site")
- role_type: One of: full_time, part_time, contract
- location: Primary work location
- required_skills: Array of required technical skills (max 15)
- preferred_skills: Array of nice-to-have skills (max 10)

IMPORTANT:
- Only extract what you can find evidence for
- For skills, only include specific technical skills, not soft skills
- For salary: parse numbers like "$500,000" as 500000 (remove commas). Convert to annual if given hourly/monthly.
- For company_name: if not explicitly named, use descriptive identifier like "Confidential - Electronic Market Maker"
- If a field is already provided and looks correct, you can skip re-extracting it

Inference hints (use with medium confidence):
- role_type: If job offers 401(k), ESPP, health insurance, equity, family leave → likely "full_time"
           If mentions "contractor", "temporary", "fixed-term" → "contract"
           If mentions "part-time", "PT", "20 hours" → "part_time"
- remote_type: "flexible work", "work persona" with remote options → "hybrid" or "remote"
             "travel required", "onsite with customers" without remote mention → likely "onsite" or "hybrid"
- seniority: "15+ years experience" → likely "principal" or "director" level
           "5-7+ years" → likely "senior" or "staff" level
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
    
    logger.info(f"Extract node started. Segmented keys: {list(segmented.keys())}")
    logger.info(f"Full text length: {len(segmented.get('full_text', ''))}")
    
    # Get the best text to analyze
    # Include benefits/compensation section explicitly (often contains salary)
    full_text = segmented.get("full_text", "")
    
    # Build context from key sections + end of posting (where salary often is)
    text_to_analyze = (
        segmented.get("requirements", "") + "\n\n" +
        segmented.get("responsibilities", "") + "\n\n" +
        segmented.get("about", "") + "\n\n" +
        segmented.get("benefits", "") + "\n\n" +  # Often contains salary info
        segmented.get("additional", "") + "\n\n" +  # "Additional Information" often has salary
        segmented.get("qualifications", "") + "\n\n" +
        full_text[:6000] + "\n\n" +  # Beginning of text
        (full_text[-3000:] if len(full_text) > 6000 else "")  # End of text (salary often here)
    )
    
    logger.info(f"Text to analyze length: {len(text_to_analyze.strip())}")
    
    if not text_to_analyze.strip():
        logger.warning("No text available for LLM extraction - returning early")
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
        logger.info("Calling LLM for extraction...")
        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(content=human_message),
        ])
        logger.info(f"LLM extraction response received, length: {len(response.content)}")
        
        # Parse JSON response
        response_text = response.content
        
        # Try to extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        llm_extracted = json.loads(response_text.strip())
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM extraction response as JSON: {e}")
        errors.append(f"Failed to parse LLM response as JSON: {str(e)}")
        llm_extracted = {}
    except Exception as e:
        logger.error(f"LLM extraction failed with exception: {e}", exc_info=True)
        errors.append(f"LLM extraction failed: {str(e)}")
        llm_extracted = {}
    
    # Merge extractions
    jobdoc = merge_extractions(extension_extracted, llm_extracted)
    logger.info(f"Extraction complete. JobDoc fields: {list(jobdoc.keys())}")
    
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
