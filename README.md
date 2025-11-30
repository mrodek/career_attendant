# Job Aid Browser Extension + API

This repo contains a Chrome/Chromium extension (under `browser_extension/`) and a Python FastAPI backend (under `api/`) with a PostgreSQL database via Docker Compose.

## Structure
- `browser_extension/` – MV3 extension UI/logic
- `api/` – FastAPI app, SQLAlchemy models
- `docker-compose.yml` – Postgres + API services
- `.env.example` – example environment variables
- `TechDebt.md` – items to tighten before prod

## Prereqs
- Docker Desktop (for db and API via Compose)
- Python 3.11 (for running tests/venv locally)

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

**In `browser_extension/popup.js`:**
```js
const CONFIG = {
  USE_PRODUCTION: false, // Set to true for Railway, false for local
  
  PRODUCTION_URL: 'https://careerattendant-production.up.railway.app/entries/',
  LOCAL_URL: 'http://localhost:8080/entries/',
  
  API_KEY: 'career_attendant_dev_987',
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

### Users Table
- `id` (VARCHAR(255)) - Primary key, accepts Clerk user_id or Chrome profile ID
- `email` (VARCHAR(255)) - Unique, required
- `username` (VARCHAR(100)) - Optional
- `full_name` (VARCHAR(255)) - Optional
- `subscription_tier` (VARCHAR(50)) - Default: 'free'
- `subscription_status` (VARCHAR(50)) - Default: 'active'
- `stripe_customer_id` (VARCHAR(255)) - Optional
- `created_at` (TIMESTAMP) - Auto-generated
- `updated_at` (TIMESTAMP) - Auto-updated
- `user_metadata` (JSON) - Default: '{}'

### Saved Jobs Table
- `id` (UUID) - Primary key
- `user_id` (VARCHAR(255)) - Foreign key to users.id (nullable)
- `job_title`, `company_name`, `job_url`, `job_description`
- `salary_range`, `location`, `remote_type`, `role_type`
- `interest_level`, `application_status`, `application_date`
- `notes`, `source`, `scraped_data` (JSON)
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
   CORS_ORIGINS=*
   # DO NOT set DROP_ALL_TABLES in production!
   ```

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
