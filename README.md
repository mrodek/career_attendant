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

## Run with Docker
1. Copy env file
   ```powershell
   Copy-Item .env.example .env
   ```
2. Start services
   ```powershell
   docker compose up --build
   ```
3. Health check
   ```powershell
   Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/health'
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

## Extension setup
- In `browser_extension/popup.js`, set API endpoint:
  ```js
  const API_URL = 'http://localhost:8080/entries';
  ```
- Add API key header in `postToApi()`:
  ```js
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'dev_api_key'
  }
  ```
- In `browser_extension/manifest.json`, set host permissions:
  ```json
  "host_permissions": ["http://localhost:8080/*"]
  ```
- Reload the extension in chrome://extensions

## API quick test (PowerShell)
```powershell
# Create entry
$body = @{ url='https://example.com'; rating=3 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://localhost:8080/entries' `
  -Headers @{ 'Content-Type'='application/json'; 'X-API-Key'='dev_api_key' } `
  -Body $body

# List entries
Invoke-RestMethod -Method Get -Uri 'http://localhost:8080/entries?page=1&pageSize=10' `
  -Headers @{ 'X-API-Key'='dev_api_key' }
```

## Notes
- CORS is permissive for local dev; see `TechDebt.md` to tighten for prod.
- API key auth is a placeholder; replace with OAuth/JWT later.
