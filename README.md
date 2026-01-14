# Career Attendant

An AI-powered job search assistant with a Chrome extension, React frontend, and FastAPI backend powered by LangGraph for intelligent job analysis.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Browser        │     │  React          │     │  FastAPI        │
│  Extension      │────▶│  Frontend       │────▶│  Backend        │
│  (Chrome MV3)   │     │  (Vite + TS)    │     │  (Python 3.11)  │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                              ┌──────────────────────────┼──────────────────────────┐
                              │                          ▼                          │
                              │  ┌─────────────────────────────────────────────┐   │
                              │  │           LangGraph Pipeline                 │   │
                              │  │                                              │   │
                              │  │  ┌─────────┐   ┌─────────┐   ┌─────────┐    │   │
                              │  │  │ Ingest  │──▶│Preprocess│──▶│ Extract │    │   │
                              │  │  └─────────┘   └─────────┘   └────┬────┘    │   │
                              │  │                                    │         │   │
                              │  │  ┌─────────┐   ┌─────────┐        │         │   │
                              │  │  │ Persist │◀──│Summarize│◀───────┘         │   │
                              │  │  └────┬────┘   └─────────┘                   │   │
                              │  │       │                                      │   │
                              │  └───────┼──────────────────────────────────────┘   │
                              │          ▼                                          │
                              │  ┌──────────────┐        ┌──────────────┐           │
                              │  │  PostgreSQL  │        │   ChromaDB   │           │
                              │  │  (Jobs, Users)│        │  (Embeddings)│           │
                              │  └──────────────┘        └──────────────┘           │
                              └─────────────────────────────────────────────────────┘
```

## Structure
- `browser_extension/` – Chrome MV3 extension for scraping job postings
- `frontend/` – React + Vite + TypeScript dashboard
- `api/` – FastAPI backend with LangGraph pipeline
  - `api/app/graphs/` – LangGraph nodes and state management
  - `api/app/routers/` – API endpoints
  - `api/app/models.py` – SQLAlchemy ORM models
- `docker-compose.yml` – PostgreSQL + API services
- `.env.example` – Environment variables template
- `TechDebt.md` – Items to address before production

## Prereqs
- Docker Desktop (for db and API via Compose)
- Node.js 18+ (for frontend)
- Python 3.11 (for running tests/venv locally)

## LangGraph Pipeline

The backend uses LangGraph (LangChain's workflow orchestration) to process job postings through an AI pipeline:

### Pipeline Nodes

| Node | Description | LLM? |
|------|-------------|------|
| **Ingest** | Validates raw text, detects source platform | No |
| **Preprocess** | Cleans HTML, segments into sections (requirements, responsibilities, benefits, etc.) | No |
| **Extract** | Uses GPT-4o-mini to extract structured fields (salary, location, skills, seniority, etc.) | ✅ |
| **Summarize** | Generates a candidate-focused job summary with key insights | ✅ |
| **Persist** | Saves job data to PostgreSQL and embeddings to ChromaDB | No |

### Extracted Fields

The LLM extraction identifies:
- **Core**: job_title, company_name, industry, location
- **Compensation**: salary_min, salary_max, salary_currency, salary_period
- **Work Arrangement**: remote_type (remote/hybrid/onsite), role_type (full_time/part_time/contract)
- **Requirements**: seniority, years_experience_min/max, required_skills, preferred_skills
- **Metadata**: posting_date

### Streaming Extraction

The `/extract/stream` endpoint uses Server-Sent Events (SSE) to stream real-time progress:
```
[ingest] → [preprocess] → [extract] → [summarize] → done
   5%          25%           60%          90%        100%
```

## Quick Start

### 1. Start Backend (Docker)

```powershell
# Copy environment file
Copy-Item .env.example .env

# Add your OpenAI API key to .env
# OPENAI_API_KEY=sk-...

# Start PostgreSQL + API
docker compose up --build -d

# Verify API is running
Invoke-RestMethod -Uri 'http://localhost:8080/health'
```

### 2. Start Frontend

```powershell
cd frontend

# Install dependencies (first time only)
npm install

# Copy environment file
Copy-Item .env.example .env.local

# Start dev server
npm run dev
```

Frontend runs at **http://localhost:5173**

### 3. Load Browser Extension

1. Open `chrome://extensions`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `browser_extension/` folder
5. Navigate to any job posting and click the extension icon

## Run with Docker (Local Development)

1. Copy env file (if needed)
   ```powershell
   Copy-Item .env.example .env
   ```

2. Start services
   ```powershell
   docker compose up --build -d
   ```
   
   **Note:** The local Docker setup includes `DROP_ALL_TABLES=true` in `docker-compose.yml`, which recreates database tables on every restart. This is convenient for development but should **never** be used in production.

3. Health check
   ```powershell
   Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/health'
   ```

4. View logs
   ```powershell
   docker logs jobaid_api --tail 50
   ```

5. Access database
   ```powershell
   docker exec -it jobaid_db psql -U jobaid -d jobaid
   ```

## Local development (API) without Docker
You can run the API locally with a virtual environment and SQLite.

### Create and activate the virtual environment
We use a named venv: `.venv-jobaidapi` inside the `api/` folder.

```powershell
cd api
python -m venv .venv-jobaidapi
.\.venv-jobaidapi\Scripts\Activate.ps1
pip install -r requirements.txt
```

If activation is blocked, allow scripts for your user (one-time):
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Run tests
```powershell
pytest -q
# or with coverage
pytest --maxfail=1 --disable-warnings -q --cov=app --cov-report=term-missing
```

### Run the API (SQLite)
```powershell
$env:API_KEY = "dev_api_key"
$env:DATABASE_URL = "sqlite+pysqlite:///./dev.db"
uvicorn app.main:app --reload --port 8080
```

### Run the API (Postgres on localhost)
If you have Postgres running (e.g., via Docker), point the API at it:
```powershell
$env:API_KEY = "dev_api_key"
$env:DATABASE_URL = "postgresql+psycopg2://jobaid:jobaidpass@localhost:5432/jobaid"
uvicorn app.main:app --reload --port 8080
```

## Browser Extension Setup

### Switching Between Local and Railway

The extension can easily switch between local development and Railway production:

**In `browser_extension/popup_v2.js`:**
```js
const CONFIG = {
  USE_PRODUCTION: false, // Set to true for Railway, false for local
  
  PRODUCTION_URL: 'https://careerattendant-production.up.railway.app/entries/',
  LOCAL_URL: 'http://localhost:8080/entries/',
  
  API_KEY: 'career_attendant_dev_987',
};
```

**In `browser_extension/background.js`:**
```js
const CONFIG = {
  // Set to true to force production API
  USE_PRODUCTION: false, // Set to true for Railway, false for local
  API_URLS: [
    'http://localhost:8080',
    'https://careerattendant-production.up.railway.app'
  ],
};
```

- **For local development:** Set `USE_PRODUCTION: false`
- **For Railway testing:** Set `USE_PRODUCTION: true`

### Load Extension in Chrome

1. Open `chrome://extensions`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `browser_extension/` folder
5. After any code changes, click the refresh icon on the extension card

### Required Permissions

The `manifest.json` includes host permissions for both environments:
```json
"host_permissions": [
  "http://localhost:8080/*",
  "https://careerattendant-production.up.railway.app/*"
]
```

## Database Schema

### Jobs Table (LLM-Extracted)
Core job data extracted by the LangGraph pipeline:
- `id` (UUID) - Primary key
- `job_url` (TEXT) - Unique, indexed
- `job_title`, `company_name`, `industry`, `location`
- **Compensation**: `salary_min`, `salary_max`, `salary_currency`, `salary_period`, `salary_raw`
- **Work Arrangement**: `remote_type`, `role_type`, `seniority`
- **Skills**: `required_skills` (JSON array), `preferred_skills` (JSON array)
- **Experience**: `years_experience_min`, `years_experience_max`
- **LLM Content**: `summary` (AI-generated), `summary_generated_at`
- **Metadata**: `source`, `posting_date`, `extraction_confidence`, `extracted_at`
- `created_at`, `updated_at` (TIMESTAMP)

### Users Table
- `id` (VARCHAR(255)) - Primary key (Clerk user_id or Chrome profile ID)
- `email` (VARCHAR(255)) - Unique, required
- `subscription_tier` (VARCHAR(50)) - Default: 'free'
- `created_at`, `updated_at` (TIMESTAMP)

### Saved Jobs Table (User-Job Relationship)
- `id` (UUID) - Primary key
- `user_id` (VARCHAR) - Foreign key to users
- `job_id` (UUID) - Foreign key to jobs
- `interest_level`, `application_status`, `notes`
- `created_at`, `updated_at` (TIMESTAMP)

## API Quick Test (PowerShell)

```powershell
# Create entry
$body = @{ 
  jobUrl = 'https://example.com/job'
  jobTitle = 'Software Engineer'
  companyName = 'Example Corp'
  interestLevel = 'high'
  userEmail = 'test@example.com'
  userId = 'test_user_123'
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri 'http://localhost:8080/entries/' `
  -Headers @{ 'Content-Type'='application/json'; 'X-API-Key'='career_attendant_dev_987' } `
  -Body $body

# List entries
Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/entries/?page=1&pageSize=10' `
  -Headers @{ 'X-API-Key'='career_attendant_dev_987' }
```

## Environment Variables

### Backend (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key for LLM extraction and summarization |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `API_KEY` | ✅ | API authentication key |
| `DEV_MODE` | No | Set `true` to bypass authentication (dev only) |
| `DROP_ALL_TABLES` | No | Set `true` to recreate DB tables on startup (dev only) |
| `CORS_ORIGINS` | No | Allowed origins, default `*` |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | ✅ | Backend API URL (e.g., `http://localhost:8080`) |
| `VITE_CLERK_PUBLISHABLE_KEY` | No | Clerk auth key (if using Clerk) |

## Notes
- CORS is permissive for local dev; see `TechDebt.md` to tighten for prod.
- API key auth is a placeholder; replace with OAuth/JWT later.

## Deployment on Railway

### API Service Setup

1. **Deploy from GitHub:**
   - Connect your GitHub repo to Railway
   - Railway auto-detects Python and installs `api/requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Required Environment Variables:**
   ```bash
   DATABASE_URL=${{Postgres.DATABASE_PRIVATE_URL}}  # Use private URL to avoid egress fees
   API_KEY=career_attendant_dev_987
   FRONTEND_URL=https://careerattendantdash-production.up.railway.app
   CORS_ORIGINS=http://localhost:5173,http://localhost:3000  # Optional: additional origins
   # DO NOT set DROP_ALL_TABLES in production!
   ```
   
   **CORS Configuration:**
   - `FRONTEND_URL` - Your production frontend URL (required for CORS)
   - `CORS_ORIGINS` - Comma-separated list of additional allowed origins (optional)
   - Extension origin is automatically added if `EXTENSION_ID` is set
   - Set `CORS_ORIGINS=*` for development only (not recommended for production)

3. **Database Setup:**
   - Add Railway's Postgres template to your project
   - Use `DATABASE_PRIVATE_URL` for internal connections (free)
   - Use `DATABASE_PUBLIC_URL` only for external tools (incurs egress fees)

### Initial Database Setup on Railway

After first deployment, if tables don't exist:

1. Go to Postgres service → **Data** tab
2. Tables will be auto-created on API startup (check API logs)
3. If you need to recreate tables:
   ```sql
   DROP TABLE IF EXISTS saved_jobs CASCADE;
   DROP TABLE IF EXISTS users CASCADE;
   ```
4. Redeploy the API service to recreate tables

### Connecting to Railway Database Locally

**For SQL clients (DBeaver, pgAdmin, etc.):**
```
Host: turntable.proxy.rlwy.net
Port: <your_assigned_port>
Database: railway
Username: postgres
Password: <from_Railway_dashboard>
```

**Using Docker with psql:**
```powershell
docker run -it --rm postgres:15 psql "<DATABASE_PUBLIC_URL>"
```

### Testing Railway Deployment

1. Set `USE_PRODUCTION: true` in `browser_extension/popup.js`
2. Reload the extension
3. Test saving a job entry
4. Check Railway API logs for success
5. Verify data in Railway Postgres → Data tab

**Note:** Always test locally first using Docker. Railway is for production deployment and testing the hosted environment.
