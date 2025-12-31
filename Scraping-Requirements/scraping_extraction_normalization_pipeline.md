# Section 3: Deterministic Extraction + Normalization Pipeline

This section defines a **board-agnostic, deterministic pipeline** for extracting and normalizing job postings and resumes into canonical `JobDoc` and `ResumeDoc` schemas.

The goal is to:
- Minimize job-board–specific logic
- Preserve raw evidence for auditability
- Produce stable, comparable documents for downstream LLM analysis

---

## 3.1 High-Level Pipeline Overview

The pipeline is intentionally staged and lossy only at the very end.

```
Fetch
  ↓
Raw Signal Extraction
  ↓
Document Assembly
  ↓
Structured Field Parsing
  ↓
Text Segmentation
  ↓
Normalization
  ↓
Skill & Signal Extraction
  ↓
Evidence Mapping & Confidence Scoring
  ↓
Emit Canonical JobDoc / ResumeDoc
```

Key principle:
> **Never destroy information early. Normalize late.**

---

## 3.2 Module Breakdown

### fetch/

Responsible for acquiring page content.

**Responsibilities**
- Retrieve HTML or rendered DOM
- Track redirects and final URLs
- Preserve headers and status codes

**Core Functions**
- `fetch_url(url) -> FetchResult`
- `fetch_rendered_url(url) -> FetchResult` (Playwright/Selenium)

---

### extract/

Pulls **raw signals** without interpretation.

**Responsibilities**
- Extract every possible machine- or human-readable signal
- Do not normalize or guess

**Core Functions**
- `extract_jsonld(html) -> list[dict]`
- `extract_meta_tags(html) -> dict`
- `extract_visible_text(html) -> str`
- `extract_headings(html) -> list[str]`

---

### detect/

Lightweight classification and metadata detection.

**Responsibilities**
- Identify job board
- Detect language

**Core Functions**
- `detect_board(hostname, html) -> board_name`
- `detect_language(text) -> lang_code`

---

### parse_job/

Structured-first field extraction.

**Responsibilities**
- Prefer structured data
- Fall back to text heuristics
- Assign confidence to each extracted field

**Precedence Order**
1. JSON-LD (`JobPosting`)
2. Embedded state JSON
3. Meta tags
4. Regex + heuristics

---

### segment/

Generic section detection and segmentation.

**Canonical Sections**
- summary
- responsibilities
- requirements
- preferred
- benefits
- about_company
- other

---

### normalize/

Canonicalization and enum mapping.

**Responsibilities**
- Convert free text into controlled vocabularies
- Normalize salary, dates, location, seniority

---

### skills/

Deterministic skill and signal extraction using a versioned taxonomy.

---

### evidence/

Traceability and confidence scoring.

---

### emit/

Final assembly into canonical schemas.

---

_End of Section 3_
