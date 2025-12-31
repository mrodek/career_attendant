"""
Node 2: preprocess_and_segment

Cleans text and segments it into logical sections.
This is deterministic - no LLM calls.
"""

import re
from typing import Any, Dict, List, Tuple

from ..state import JobIntakeState, SegmentedText, DocStats


# Common section headers in job postings
SECTION_PATTERNS = [
    (r"(?i)\b(about\s+(?:the\s+)?(?:job|role|position|opportunity))\b", "about"),
    (r"(?i)\b(responsibilities|what\s+you(?:'ll)?\s+(?:do|be\s+doing)|your\s+role)\b", "responsibilities"),
    (r"(?i)\b(requirements|qualifications|what\s+you(?:'ll)?\s+need|what\s+we(?:'re)?\s+looking\s+for|must\s+have)\b", "requirements"),
    (r"(?i)\b(nice\s+to\s+have|preferred|bonus|ideal)\b", "qualifications"),
    (r"(?i)\b(benefits|perks|what\s+we\s+offer|compensation|salary|pay\s+range|why\s+(?:is\s+this|join|work))\b", "benefits"),
    (r"(?i)\b(about\s+(?:the\s+)?company|about\s+us|who\s+we\s+are)\b", "company_info"),
    (r"(?i)\b(additional\s+information|other\s+information)\b", "additional"),
]


def clean_text(text: str) -> str:
    """Clean and normalize the raw text."""
    if not text:
        return ""
    
    # Decode common HTML entities
    import html
    text = html.unescape(text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove common artifacts
    text = re.sub(r'(?i)(show more|show less|easy apply|apply now)', '', text)
    
    # Trim
    return text.strip()


def detect_language(text: str) -> str:
    """Simple language detection (English assumed for now)."""
    # Could integrate langdetect library later
    return "en"


def count_tokens(text: str) -> int:
    """Estimate token count (rough approximation)."""
    # Approximate: ~4 chars per token for English
    return len(text) // 4


def segment_text(text: str) -> Tuple[SegmentedText, int]:
    """
    Split text into logical sections based on common headers.
    
    Returns:
        - SegmentedText dict with sections
        - Number of sections found
    """
    segments: SegmentedText = {"full_text": text}
    section_count = 0
    
    # Find section boundaries
    section_starts: List[Tuple[int, str, str]] = []  # (position, section_name, header_text)
    
    for pattern, section_name in SECTION_PATTERNS:
        for match in re.finditer(pattern, text):
            section_starts.append((match.start(), section_name, match.group()))
    
    # Sort by position
    section_starts.sort(key=lambda x: x[0])
    
    # Extract sections
    for i, (start_pos, section_name, header) in enumerate(section_starts):
        # Find end position (next section start or end of text)
        if i + 1 < len(section_starts):
            end_pos = section_starts[i + 1][0]
        else:
            end_pos = len(text)
        
        # Extract section content (skip the header itself)
        content = text[start_pos + len(header):end_pos].strip()
        
        if content and len(content) > 50:  # Minimum content threshold
            if section_name not in segments or len(content) > len(segments.get(section_name, "")):
                segments[section_name] = content
                section_count += 1
    
    return segments, section_count


def preprocess_and_segment(state: JobIntakeState) -> Dict[str, Any]:
    """
    Clean and segment the raw job text.
    
    Inputs:
        - raw_text: The scraped text from the extension
    
    Outputs:
        - segmented: SegmentedText with sections
        - doc_stats: Statistics about the document
        - current_node: Updated tracker
    """
    raw_text = state.get("raw_text", "")
    errors = list(state.get("errors", []))
    
    # Clean the text
    cleaned_text = clean_text(raw_text)
    
    if not cleaned_text:
        errors.append("No text content after cleaning")
        return {
            "segmented": {"full_text": ""},
            "doc_stats": {},
            "current_node": "preprocess_and_segment",
            "errors": errors,
        }
    
    # Segment into sections
    segmented, section_count = segment_text(cleaned_text)
    
    # Calculate stats
    doc_stats: DocStats = {
        "char_count": len(cleaned_text),
        "word_count": len(cleaned_text.split()),
        "token_count": count_tokens(cleaned_text),
        "section_count": section_count,
        "language": detect_language(cleaned_text),
    }
    
    return {
        "segmented": segmented,
        "doc_stats": doc_stats,
        "current_node": "preprocess_and_segment",
        "errors": errors,
    }
