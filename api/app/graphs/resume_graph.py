from typing import TypedDict, Optional
import json
import logging

from langgraph.graph import StateGraph, END

logger = logging.getLogger("api")

# State dictionary for the resume processing graph
class ResumeProcessingState(TypedDict, total=False):
    user_id: str
    resume_id: str
    file_path: str
    file_type: str
    raw_text: Optional[str]
    llm_extracted_json: Optional[dict]
    error_message: Optional[str]
    processing_status: str

# LLM prompt for resume extraction
RESUME_EXTRACTION_PROMPT = """You are an expert resume analyzer. Extract detailed, structured information from this resume/CV.

CRITICAL: You must ONLY extract information that is EXPLICITLY present in the text. Do NOT infer, calculate, or fabricate any data.

Resume/CV:
\"\"\"
{resume_text}
\"\"\"

Return valid JSON with this exact structure:

{{
  "candidate_profile": {{
    "name": "full name exactly as written or null",
    "email": "email address exactly as written or null",
    "phone": "phone number exactly as written or null",
    "location": {{
      "city": "city name exactly as written or null",
      "state_province": "state/province exactly as written or null",
      "country": "country exactly as written or null"
    }},
    "linkedin_url": "LinkedIn profile URL exactly as written or null",
    "portfolio_url": "portfolio/personal website URL exactly as written or null",
    "willing_to_relocate": true | false | "unknown",
    "current_title": "most recent job title exactly as written or null",
    "years_total_experience": "number (ONLY if explicitly stated, otherwise calculate from work history dates)"
  }},

  "professional_summary": {{
    "summary_text": "exact text of professional summary/objective if present, or null",
    "key_strengths_mentioned": ["only strengths explicitly stated in summary"],
    "career_focus": "brief description ONLY from what is explicitly stated"
  }},

  "work_history": [
    {{
      "company_name": "company name EXACTLY as written",
      "job_title": "job title EXACTLY as written",
      "location": "location EXACTLY as written or null",
      "start_date": "YYYY-MM or YYYY EXACTLY as written",
      "end_date": "YYYY-MM or YYYY or 'present' EXACTLY as written",
      "duration_months": "number (calculate from start/end dates only)",
      "is_current_role": true | false,
      "employment_type": "full_time | part_time | contract | internship | freelance | unknown",
      "responsibilities": [
        {{
          "text": "EXACT bullet point text - do not paraphrase",
          "category": "technical_execution | leadership | strategy | collaboration | customer_facing | process_improvement | individual_contribution",
          "contains_metrics": true | false,
          "source_quote": "exact phrase containing any numbers mentioned"
        }}
      ],
      "achievements": [
        {{
          "text": "EXACT achievement text - do not paraphrase",
          "achievement_type": "revenue_growth | cost_reduction | efficiency_gain | scale | team_building | innovation | customer_satisfaction | quality_improvement | other",
          "quantified": true | false,
          "source_quote": "exact phrase where numbers appear",
          "metrics_extracted": {{
            "metric_type": "percentage | dollar_amount | time_saved | scale_number | other",
            "value": "number or null (ONLY if number explicitly appears in text)",
            "baseline": "before state if mentioned or null",
            "result": "after state if mentioned"
          }}
        }}
      ],
      "technologies_used": ["ONLY technologies explicitly mentioned in this role's description"]
    }}
  ],

  "education": [
    {{
      "institution": "school name EXACTLY as written",
      "degree_type": "high_school | associate | bachelor | master | phd | certificate | bootcamp",
      "degree_name": "degree name EXACTLY as written",
      "field_of_study": "major/field EXACTLY as written",
      "graduation_year": "number or null (ONLY if explicitly stated)",
      "gpa": "number or null (ONLY if explicitly stated)",
      "honors": ["ONLY honors/awards explicitly listed"],
      "relevant_coursework": ["ONLY if explicitly listed"]
    }}
  ],

  "skills_inventory": {{
    "technical_skills": [
      {{
        "skill_name": "skill name EXACTLY as written",
        "category": "programming_language | framework | tool | platform | methodology | domain_knowledge | other",
        "proficiency_claimed": "beginner | intermediate | advanced | expert | unspecified",
        "years_experience": "number or null (ONLY if explicitly stated - do NOT calculate)",
        "evidence_strength": "strong | moderate | weak | claimed_only",
        "is_inferred": true | false,
        "source_quote": "exact phrase where skill is mentioned or 'inferred from [context]'"
      }}
    ],
    "soft_skills": [
      {{
        "skill_name": "soft skill name",
        "evidence": ["specific examples from resume where demonstrated"],
        "evidence_strength": "strong | moderate | weak | claimed_only"
      }}
    ],
    "languages": [
      {{
        "language": "language name EXACTLY as written",
        "proficiency": "basic | conversational | professional | fluent | native"
      }}
    ],
    "certifications": [
      {{
        "name": "certification name EXACTLY as written",
        "issuing_organization": "org name EXACTLY as written or null",
        "date_obtained": "YYYY-MM or YYYY EXACTLY as written or null",
        "credential_id": "ID if provided or null"
      }}
    ]
  }},

  "leadership_profile": {{
    "has_leadership_experience": true | false,
    "leadership_summary": {{
      "max_team_size_managed": "number or null (ONLY from explicit mentions like 'led team of X')",
      "years_in_leadership": "number or null (ONLY if explicitly stated)",
      "leadership_levels": ["levels based on actual titles held"]
    }},
    "people_management_evidence": [
      {{
        "evidence_text": "EXACT text showing people management",
        "role": "which job this was from",
        "team_size": "number or null (ONLY if explicitly stated)",
        "source_quote": "exact phrase"
      }}
    ],
    "hiring_experience": "true | false (ONLY if explicitly mentioned)",
    "budget_responsibility": {{
      "has_budget_experience": "true | false (ONLY if explicitly mentioned)",
      "max_budget_managed": "number or null (ONLY if explicitly stated)",
      "source_quote": "exact phrase where budget is mentioned"
    }}
  }},

  "career_trajectory": {{
    "total_jobs": "number (count from work history)",
    "average_tenure_months": "number (calculated from work history)",
    "title_progression": ["chronological list of actual titles from work history"],
    "seniority_assessment": "entry | junior | mid | senior | staff | lead | principal | director | vp | c_level"
  }},

  "projects_portfolio": [
    {{
      "project_name": "project name EXACTLY as written",
      "role": "role EXACTLY as stated",
      "technologies": ["ONLY technologies explicitly mentioned"],
      "outcomes": "ONLY outcomes explicitly stated",
      "url": "link EXACTLY as written or null"
    }}
  ],

  "parsing_metadata": {{
    "resume_format": "chronological | functional | combination | unknown",
    "overall_quality": "excellent | good | adequate | poor",
    "parsing_confidence": "0.0-1.0",
    "inferred_data_points": ["list all data points that were inferred vs. explicit"]
  }}
}}

GROUNDING REQUIREMENTS - CRITICAL:

1. ONLY EXTRACT EXPLICIT INFORMATION - If something is IMPLIED but not STATED, mark it as inferred
2. NEVER FABRICATE - Years of experience ONLY if explicitly stated, proficiency levels ONLY if explicitly claimed
3. NUMERIC VALUES MUST HAVE SOURCE QUOTES - For ANY number you extract, provide source_quote with EXACT text
4. Copy bullet points EXACTLY - do not paraphrase
5. For skills: If skill name NOT found in text, set "is_inferred": true and explain why

Return ONLY the JSON object. No markdown formatting, no additional text."""

from ..text_extractor import extract_text_from_pdf, extract_text_from_docx
from .config import get_llm


# === Graph Nodes ===

def extract_text_node(state: ResumeProcessingState) -> ResumeProcessingState:
    """Extracts text from the resume file."""
    logger.info(f"Extracting text from resume {state.get('resume_id')}")
    
    try:
        file_path = state["file_path"]
        file_type = state.get("file_type", "")
        
        with open(file_path, "rb") as f:
            content = f.read()
        
        if "pdf" in file_type.lower():
            raw_text = extract_text_from_pdf(content)
        elif "document" in file_type.lower() or file_path.endswith(".docx"):
            raw_text = extract_text_from_docx(content)
        else:
            # Try PDF first, fallback to DOCX
            try:
                raw_text = extract_text_from_pdf(content)
            except:
                raw_text = extract_text_from_docx(content)
        
        logger.info(f"Extracted {len(raw_text)} characters from resume")
        return {**state, "raw_text": raw_text, "processing_status": "processing"}
    
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return {**state, "error_message": f"Text extraction failed: {str(e)}", "processing_status": "failed"}


def parse_with_llm_node(state: ResumeProcessingState) -> ResumeProcessingState:
    """Parses the raw text using the LLM to extract structured data."""
    if state.get("error_message"):
        return state
    
    raw_text = state.get("raw_text")
    if not raw_text:
        return {**state, "error_message": "No text extracted from resume", "processing_status": "failed"}
    
    logger.info(f"Running LLM extraction for resume {state.get('resume_id')}")
    
    try:
        llm = get_llm()
        prompt = RESUME_EXTRACTION_PROMPT.format(resume_text=raw_text)
        
        # Use LangChain's structured output
        from langchain_core.messages import HumanMessage, SystemMessage
        
        messages = [
            SystemMessage(content="You are an expert resume parser. Return only valid JSON."),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        response_text = response.content
        
        # Parse JSON from response
        # Handle markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        llm_extracted_json = json.loads(response_text.strip())
        
        logger.info(f"LLM extraction completed for resume {state.get('resume_id')}")
        return {**state, "llm_extracted_json": llm_extracted_json, "processing_status": "completed"}
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        return {**state, "error_message": f"Failed to parse LLM response: {str(e)}", "processing_status": "failed"}
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return {**state, "error_message": f"LLM extraction failed: {str(e)}", "processing_status": "failed"}


def save_to_db_node(db_url: str):
    """Factory function that creates a save node with database access."""
    
    def _save_to_db(state: ResumeProcessingState) -> ResumeProcessingState:
        """Saves the extracted data to the database."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from ..models import Resume
        
        logger.info(f"Saving resume {state.get('resume_id')} to database")
        
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            resume = db.query(Resume).filter(Resume.id == state["resume_id"]).first()
            if resume:
                if state.get("llm_extracted_json"):
                    # Encrypt the JSON data before saving
                    from ..encryption import encryption
                    encrypted_json = encryption.encrypt_json(state["llm_extracted_json"])
                    resume.llm_extracted_json = encrypted_json
                    
                if state.get("raw_text"):
                    # Encrypt the raw text before saving
                    from ..encryption import encryption
                    encrypted_text = encryption.encrypt_text(state["raw_text"])
                    resume.raw_text = encrypted_text
                
                if state.get("error_message"):
                    resume.processing_status = "failed"
                    resume.error_message = state["error_message"]
                else:
                    resume.processing_status = "completed"
                
                db.commit()
                logger.info(f"Resume {state.get('resume_id')} saved with status: {resume.processing_status}")
            else:
                logger.warning(f"Resume {state.get('resume_id')} not found in database")
        except Exception as e:
            logger.error(f"Failed to save resume to database: {e}")
            db.rollback()
        finally:
            db.close()
        
        return state
    
    return _save_to_db


def create_resume_graph(db_url: str):
    """Creates and returns the resume processing graph."""
    workflow = StateGraph(ResumeProcessingState)

    workflow.add_node("extract_text", extract_text_node)
    workflow.add_node("parse_with_llm", parse_with_llm_node)
    workflow.add_node("save_to_db", save_to_db_node(db_url))

    workflow.set_entry_point("extract_text")
    workflow.add_edge("extract_text", "parse_with_llm")
    workflow.add_edge("parse_with_llm", "save_to_db")
    workflow.add_edge("save_to_db", END)

    return workflow.compile()


def run_resume_processing_sync(
    resume_id: str,
    user_id: str,
    file_path: str,
    file_type: str,
    db_url: str,
) -> ResumeProcessingState:
    """
    Synchronous function to run resume processing.
    Use this from background tasks.
    """
    logger.info(f"Starting resume processing for {resume_id}")
    
    graph = create_resume_graph(db_url)
    
    initial_state: ResumeProcessingState = {
        "resume_id": resume_id,
        "user_id": user_id,
        "file_path": file_path,
        "file_type": file_type,
        "processing_status": "processing",
    }
    
    final_state = graph.invoke(initial_state)
    
    logger.info(f"Resume processing completed for {resume_id}: {final_state.get('processing_status')}")
    return final_state

