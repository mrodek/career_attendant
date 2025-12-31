"""
Node 5: generate_job_summary

Uses LLM to create a concise, actionable summary of the job posting.
"""

import json
from typing import Any, Dict

from langchain_core.messages import SystemMessage, HumanMessage

from ..state import JobIntakeState
from ..config import get_llm_creative


SUMMARY_SYSTEM_PROMPT = """You are a career advisor helping job seekers quickly understand job opportunities.

Create a concise, actionable summary of the job posting that helps a candidate decide if they should apply.

Your summary should include:

1. **Role Overview** (2-3 sentences): What is this job really about? What's the core mission?

2. **Key Responsibilities** (4-6 bullets): The most important things this person will do day-to-day

3. **Must-Have Qualifications** (3-5 bullets): Non-negotiable requirements

4. **Nice-to-Haves** (2-3 bullets): Things that would give a candidate an edge

5. **What Success Looks Like** (2-3 sentences): How would someone excel in this role? What would make them a top performer?

6. **Red Flags / Considerations** (1-2 bullets, optional): Anything a candidate should be aware of (travel, on-call, relocation, etc.)

Format your response as markdown with clear headers.

Be direct and specific. Avoid generic corporate speak. Focus on what would actually help someone decide if this job is right for them.
"""


def generate_job_summary(state: JobIntakeState) -> Dict[str, Any]:
    """
    Generate a concise, actionable summary of the job posting.
    
    Inputs:
        - segmented: Segmented text sections
        - jobdoc: Extracted job document fields
    
    Outputs:
        - job_summary: Markdown summary
        - success_criteria: What success looks like
        - current_node: Updated tracker
    """
    errors = list(state.get("errors", []))
    segmented = state.get("segmented", {})
    jobdoc = state.get("jobdoc", {})
    
    # Build context for summarization
    job_context = f"""
Job Title: {jobdoc.get('job_title', 'Unknown')}
Company: {jobdoc.get('company_name', 'Unknown')}
Location: {jobdoc.get('location', 'Unknown')}
Remote: {jobdoc.get('remote_type', 'Unknown')}
Seniority: {jobdoc.get('seniority', 'Unknown')}
Salary Range: ${jobdoc.get('salary_min', '?')} - ${jobdoc.get('salary_max', '?')}
Required Skills: {', '.join(jobdoc.get('required_skills', [])[:10])}
"""
    
    # Get the full text for summarization
    full_text = segmented.get("full_text", "")
    
    if not full_text:
        errors.append("No text available for summarization")
        return {
            "job_summary": "",
            "success_criteria": "",
            "current_node": "generate_job_summary",
            "errors": errors,
        }
    
    human_message = f"""Create a summary for this job posting.

Context:
{job_context}

Full Job Description:
---
{full_text[:10000]}
---

Create a concise, actionable summary."""

    try:
        llm = get_llm_creative()
        response = llm.invoke([
            SystemMessage(content=SUMMARY_SYSTEM_PROMPT),
            HumanMessage(content=human_message),
        ])
        
        job_summary = response.content
        
        # Extract success criteria section if present
        success_criteria = ""
        if "success looks like" in job_summary.lower():
            # Try to extract that section
            lines = job_summary.split("\n")
            capture = False
            success_lines = []
            for line in lines:
                if "success looks like" in line.lower():
                    capture = True
                    continue
                if capture:
                    if line.startswith("#") or line.startswith("**"):
                        break
                    success_lines.append(line)
            success_criteria = "\n".join(success_lines).strip()
        
    except Exception as e:
        errors.append(f"Summary generation failed: {str(e)}")
        job_summary = ""
        success_criteria = ""
    
    return {
        "job_summary": job_summary,
        "success_criteria": success_criteria,
        "current_node": "generate_job_summary",
        "errors": errors,
    }
