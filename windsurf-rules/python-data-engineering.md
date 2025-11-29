# Data Engineering (Python): Modern Tooling Standards
1. Data Validation: Pydantic Is Mandatory
* ALL data schemas, API request bodies, and configuration objects MUST use Pydantic BaseModel.
* Rationale: Ensures type-driven validation, robust parsing, and strict data integrity.
* All functions MUST use modern Python type hints.
* Anti-Pattern (BLOCK): Do NOT pass raw dictionaries (dict) as structured data between services — always define a BaseModel.

2. API Calls: httpx Replaces requests
* ALL HTTP client calls MUST use httpx.
* Rationale: Supports async/await, HTTP/2, and high-performance non-blocking I/O.
* Anti-Pattern (BLOCK): Do NOT use requests in new code.