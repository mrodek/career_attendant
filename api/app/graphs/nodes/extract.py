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


COMPREHENSIVE_JOB_PARSING_PROMPT = """
You are an expert job requirements analyzer. Extract detailed, structured information from this job posting.

Job Posting:
\"\"\"
{job_posting_text}
\"\"\"

Return valid JSON with this exact structure:

{{
  "metadata": {{
    "job_title": "exact title",
    "company_name": "company name or null",
    "location": {{
      "city": "city name or null",
      "state_province": "state/province or null", 
      "country": "country or null",
      "is_remote": true | false,
      "remote_policy": "fully_remote" | "hybrid_flexible" | "hybrid_fixed" | "onsite" | "unknown"
    }},
    "employment_type": "full_time" | "part_time" | "contract" | "temporary" | "internship",
    "job_function": "engineering" | "sales" | "marketing" | "operations" | "finance" | "hr" | "product" | "design" | "customer_success" | "other",
    "industry": "best guess of company industry or null"
  }},

  "requirements": [
    {{
      "requirement_text": "exact text from posting",
      "requirement_type": "technical_skill" | "tool_technology" | "soft_skill" | "years_experience" | "domain_experience" | "industry_experience" | "education" | "certification" | "language" | "leadership_experience" | "team_management" | "budget_responsibility" | "achievement_track_record" | "methodology" | "other",
      "category": "must_have" | "strongly_preferred" | "nice_to_have",
      "importance_score": 1-10,
      "specificity": "very_specific" | "somewhat_specific" | "general",
      "quantifiable": true | false,
      "keywords": ["list", "of", "key", "terms"]
    }}
  ],

  "experience_profile": {{
    "years_required": {{
      "minimum": number or null,
      "maximum": number or null,
      "preferred": number or null
    }},
    "seniority_level": "intern" | "entry" | "junior" | "mid" | "senior" | "staff" | "lead" | "principal" | "director" | "vp" | "c_level",
    "relevant_experience_types": [
      {{
        "type": "brief description of experience type needed",
        "importance": 1-10
      }}
    ],
    "industry_experience_needed": ["list of industries"] or [],
    "company_stage_experience": "startup" | "scaleup" | "growth" | "enterprise" | "any" | null
  }},

  "education": {{
    "degree_required": true | false,
    "degree_level": "high_school" | "associate" | "bachelor" | "master" | "phd" | null,
    "field_of_study": ["list of acceptable fields"] or [],
    "alternative_accepted": "equivalent experience" | "certifications" | "none" | null,
    "certifications": [
      {{
        "name": "certification name",
        "required": true | false
      }}
    ]
  }},

  "skills_breakdown": {{
    "technical_skills": [
      {{
        "skill_name": "skill name",
        "proficiency_expected": "beginner" | "intermediate" | "advanced" | "expert" | "unspecified",
        "years_expected": number or null,
        "is_required": true | false,
        "category": "programming_language" | "framework" | "tool" | "platform" | "methodology" | "domain_knowledge"
      }}
    ],
    "soft_skills": ["list of soft skills mentioned"],
    "languages": [
      {{
        "language": "language name",
        "proficiency": "basic" | "professional" | "fluent" | "native",
        "required": true | false
      }}
    ]
  }},

  "responsibilities": [
    {{
      "responsibility_text": "exact text from posting",
      "category": "technical_execution" | "leadership" | "strategy" | "collaboration" | "individual_contribution" | "customer_facing" | "internal_process",
      "scope_indicators": {{
        "team_size": number or null,
        "budget": number or null,
        "customer_base": "description or null",
        "cross_functional": true | false
      }}
    }}
  ],

  "achievement_indicators": [
    {{
      "achievement_type": "revenue_growth" | "cost_reduction" | "team_building" | "process_improvement" | "product_launch" | "scale" | "innovation" | "customer_satisfaction" | "other",
      "description": "what success looks like for this role",
      "quantifiable": true | false
    }}
  ],

  "compensation": {{
    "salary": {{
      "min": number or null,
      "max": number or null,
      "currency": "USD" | "EUR" | "GBP" | other | null,
      "period": "annual" | "hourly" | "daily" | null
    }},
    "equity": {{
      "mentioned": true | false,
      "type": "stock_options" | "rsu" | "equity_grant" | "unspecified" | null
    }},
    "bonus_mentioned": true | false,
    "benefits_highlighted": ["list of notable benefits"] or []
  }},

  "culture_values": {{
    "company_values": ["values explicitly mentioned"],
    "work_style": ["collaborative" | "autonomous" | "fast_paced" | "structured" | "flexible" | "mission_driven" | "data_driven" | "customer_centric" | "innovative" | "other"],
    "team_size": "small" | "medium" | "large" | null,
    "growth_stage": "seed" | "series_a" | "series_b" | "series_c_plus" | "public" | "established" | null,
    "culture_keywords": ["keywords that signal culture"]
  }},

  "application_details": {{
    "visa_sponsorship": true | false | "unknown",
    "security_clearance": true | false,
    "background_check": true | false | "unknown",
    "deadline": "date or null",
    "referral_bonus_mentioned": true | false
  }},

  "parsing_confidence": {{
    "overall_confidence": 0.0-1.0,
    "ambiguous_requirements": ["list any unclear requirements"],
    "missing_information": ["list key info not found in posting"]
  }}
}}

CRITICAL INSTRUCTIONS:

1. IMPORTANCE SCORING RULES:
   - 10: Appears in top 3 requirements, uses "must", "required", "critical"
   - 8-9: Appears in requirements section, emphasized
   - 6-7: Mentioned in job description body
   - 4-5: Mentioned in "nice to have" or "preferred"
   - 1-3: Mentioned once briefly or in passing

2. REQUIREMENT CATEGORIZATION:
   - "must_have": Uses language like "required", "must have", "essential"
   - "strongly_preferred": Uses "strongly preferred", "highly desired"
   - "nice_to_have": Uses "nice to have", "plus", "bonus"

3. SENIORITY INFERENCE:
   - Look at title keywords: "junior", "senior", "lead", "principal", "staff"
   - Cross-reference with years of experience
   - Consider responsibility scope (team size, budget, strategic impact)

4. ACHIEVEMENT INDICATORS:
   - Look for phrases like "track record of", "proven ability to", "history of"
   - Extract what outcomes indicate success in this role

5. CULTURE SIGNALS:
   - Note tone and language (formal vs casual)
   - Company values explicitly stated
   - Work environment descriptions
   - Benefits that signal culture (unlimited PTO, learning budget, etc.)

6. HANDLE AMBIGUITY:
   - If something is unclear, note it in "ambiguous_requirements"
   - Use null for truly unknown values
   - Provide confidence scores for subjective assessments

7. EXTRACT EVERYTHING:
   - Even minor requirements matter for matching
   - Capture both explicit and implicit requirements
   - Note what's missing (e.g., no salary = transparency issue)

Return ONLY the JSON object, no markdown formatting, no additional text.
"""


# Legacy prompt kept for reference
EXTRACTION_SYSTEM_PROMPT_LEGACY = """You are a job posting analyzer. Extract structured information from job descriptions.
(Legacy prompt - kept for reference only)
"""


def map_comprehensive_to_jobdoc(
    comprehensive: Dict[str, Any],
    extension_extracted: JobDocPartial,
) -> JobDocPartial:
    """
    Map fields from the comprehensive analysis JSON to the legacy JobDocPartial format.
    
    This provides backward compatibility with downstream nodes (summarize, persist)
    that expect the flat jobdoc structure.
    
    Priority: LLM-extracted values override extension values when available.
    """
    jobdoc: JobDocPartial = dict(extension_extracted)
    
    # Extract from metadata
    metadata = comprehensive.get("metadata", {})
    if metadata.get("job_title"):
        jobdoc["job_title"] = metadata["job_title"]
    if metadata.get("company_name"):
        jobdoc["company_name"] = metadata["company_name"]
    if metadata.get("industry"):
        jobdoc["industry"] = metadata["industry"]
    
    # Location
    location = metadata.get("location", {})
    if location:
        location_parts = []
        if location.get("city"):
            location_parts.append(location["city"])
            jobdoc["location_city"] = location["city"]
        if location.get("state_province"):
            location_parts.append(location["state_province"])
        if location.get("country"):
            location_parts.append(location["country"])
            jobdoc["location_country"] = location["country"]
        if location_parts:
            jobdoc["location"] = ", ".join(location_parts)
        
        # Map remote_policy to remote_type
        remote_policy = location.get("remote_policy")
        if remote_policy:
            if remote_policy == "fully_remote":
                jobdoc["remote_type"] = "remote"
            elif remote_policy in ("hybrid_flexible", "hybrid_fixed"):
                jobdoc["remote_type"] = "hybrid"
            elif remote_policy == "onsite":
                jobdoc["remote_type"] = "onsite"
    
    # Employment type -> role_type
    employment_type = metadata.get("employment_type")
    if employment_type:
        jobdoc["role_type"] = employment_type
    
    # Experience profile
    exp_profile = comprehensive.get("experience_profile", {})
    years_required = exp_profile.get("years_required", {})
    if years_required.get("minimum") is not None:
        jobdoc["years_experience_min"] = years_required["minimum"]
    if years_required.get("maximum") is not None:
        jobdoc["years_experience_max"] = years_required["maximum"]
    if exp_profile.get("seniority_level"):
        jobdoc["seniority"] = exp_profile["seniority_level"]
    
    # Compensation
    compensation = comprehensive.get("compensation", {})
    salary = compensation.get("salary", {})
    if salary.get("min") is not None:
        jobdoc["salary_min"] = salary["min"]
    if salary.get("max") is not None:
        jobdoc["salary_max"] = salary["max"]
    if salary.get("currency"):
        jobdoc["salary_currency"] = salary["currency"]
    if salary.get("period"):
        jobdoc["salary_period"] = salary["period"]
    
    # Skills
    skills_breakdown = comprehensive.get("skills_breakdown", {})
    technical_skills = skills_breakdown.get("technical_skills", [])
    if technical_skills:
        required = [s["skill_name"] for s in technical_skills if s.get("is_required")]
        preferred = [s["skill_name"] for s in technical_skills if not s.get("is_required")]
        if required:
            jobdoc["required_skills"] = required[:15]  # Cap at 15
        if preferred:
            jobdoc["preferred_skills"] = preferred[:10]  # Cap at 10
    
    return jobdoc


def build_extraction_evidence_from_comprehensive(comprehensive: Dict[str, Any]) -> List[dict]:
    """Build evidence list from comprehensive analysis."""
    evidence = []
    
    # Add confidence info
    parsing_confidence = comprehensive.get("parsing_confidence", {})
    overall_confidence = parsing_confidence.get("overall_confidence", 0.5)
    
    # Add key extracted fields as evidence
    metadata = comprehensive.get("metadata", {})
    for field in ["job_title", "company_name", "industry"]:
        if metadata.get(field):
            evidence.append({
                "field": field,
                "value": metadata[field],
                "evidence": "Extracted from job posting",
                "confidence": "high" if overall_confidence > 0.7 else "medium",
                "source": "llm_comprehensive",
            })
    
    # Add requirements count
    requirements = comprehensive.get("requirements", [])
    if requirements:
        evidence.append({
            "field": "requirements_count",
            "value": len(requirements),
            "evidence": f"Extracted {len(requirements)} requirements",
            "confidence": "high",
            "source": "llm_comprehensive",
        })
    
    return evidence


def extract_structured_fields(state: JobIntakeState) -> Dict[str, Any]:
    """
    Use LLM to extract comprehensive structured fields from job text.
    
    This node:
    1. Takes the segmented text and extension-extracted fields
    2. Uses the comprehensive parsing prompt to extract detailed job information
    3. Stores the full JSON in comprehensive_analysis for job fit scoring
    4. Maps key fields to jobdoc for backward compatibility
    
    Inputs:
        - segmented: Segmented text sections
        - extension_extracted: Fields already extracted by extension
    
    Outputs:
        - comprehensive_analysis: Full JSON from comprehensive extraction
        - llm_extracted: Legacy field (same as comprehensive_analysis)
        - extraction_evidence: Evidence for each extraction
        - jobdoc: Mapped JobDoc for backward compatibility
        - current_node: Updated tracker
    """
    errors = list(state.get("errors", []))
    segmented = state.get("segmented", {})
    extension_extracted = state.get("extension_extracted", {})
    
    logger.info(f"Extract node started. Segmented keys: {list(segmented.keys())}")
    logger.info(f"Full text length: {len(segmented.get('full_text', ''))}")
    
    # Get the full text to analyze
    full_text = segmented.get("full_text", "")
    
    # Build comprehensive text from all sections
    text_to_analyze = (
        segmented.get("requirements", "") + "\n\n" +
        segmented.get("responsibilities", "") + "\n\n" +
        segmented.get("about", "") + "\n\n" +
        segmented.get("benefits", "") + "\n\n" +
        segmented.get("additional", "") + "\n\n" +
        segmented.get("qualifications", "") + "\n\n" +
        full_text[:8000]  # Include as much context as possible
    )
    
    logger.info(f"Text to analyze length: {len(text_to_analyze.strip())}")
    
    if not text_to_analyze.strip():
        logger.warning("No text available for LLM extraction - returning early")
        errors.append("No text available for LLM extraction")
        return {
            "comprehensive_analysis": {},
            "llm_extracted": {},
            "extraction_evidence": [],
            "jobdoc": extension_extracted,
            "current_node": "extract_structured_fields",
            "errors": errors,
        }
    
    # Format the prompt with the job posting text
    formatted_prompt = COMPREHENSIVE_JOB_PARSING_PROMPT.replace(
        "{job_posting_text}", 
        text_to_analyze[:12000]  # Cap at 12k chars to leave room for response
    )

    try:
        logger.info("Calling LLM for comprehensive extraction...")
        llm = get_llm()
        response = llm.invoke([
            HumanMessage(content=formatted_prompt),
        ])
        logger.info(f"LLM extraction response received, length: {len(response.content)}")
        
        # Parse JSON response
        response_text = response.content
        
        # Try to extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        comprehensive_analysis = json.loads(response_text.strip())
        logger.info(f"Comprehensive extraction successful. Keys: {list(comprehensive_analysis.keys())}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM extraction response as JSON: {e}")
        logger.error(f"Response text (first 500 chars): {response_text[:500] if 'response_text' in dir() else 'N/A'}")
        errors.append(f"Failed to parse LLM response as JSON: {str(e)}")
        comprehensive_analysis = {}
    except Exception as e:
        logger.error(f"LLM extraction failed with exception: {e}", exc_info=True)
        errors.append(f"LLM extraction failed: {str(e)}")
        comprehensive_analysis = {}
    
    # Map comprehensive analysis to legacy jobdoc format for backward compatibility
    jobdoc = map_comprehensive_to_jobdoc(comprehensive_analysis, extension_extracted)
    logger.info(f"Extraction complete. JobDoc fields: {list(jobdoc.keys())}")
    
    # Build evidence from comprehensive analysis
    extraction_evidence = build_extraction_evidence_from_comprehensive(comprehensive_analysis)
    
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
        "comprehensive_analysis": comprehensive_analysis,
        "llm_extracted": comprehensive_analysis,  # Legacy compatibility
        "extraction_evidence": extraction_evidence,
        "jobdoc": jobdoc,
        "current_node": "extract_structured_fields",
        "errors": errors,
    }
