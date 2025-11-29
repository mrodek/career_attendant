# ADR-001: Railway Hosting Strategy for API and Database

Status: Accepted

## Context

The project needs a production-ready hosting strategy for the JobAid API and its PostgreSQL database. Currently:

- The API is a FastAPI app located under `api/` with a small `requirements.txt` and `uvicorn` entrypoint.
- Local development uses Docker Compose to run the API and a Postgres container together.
- Railway is the target platform for production hosting. Railway supports both Docker-based services and build-from-source services, as well as a managed Postgres template.

Key considerations:

- Minimize operational overhead and complexity.
- Support fast, iterative deployments from GitHub.
- Avoid over-optimizing for container portability before the product is validated.
- Leverage Railway’s strengths (managed DB, simple build pipeline) where possible.

## Decision

1. **API Hosting on Railway**

   - Deploy the FastAPI application as a **non-Docker Railway service built from source**, rather than as a custom Docker container.
   - Railway will:
     - Detect Python in the `api/` directory.
     - Install dependencies from `api/requirements.txt`.
     - Start the application with a command such as:
       - `uvicorn app.main:app --host 0.0.0.0 --port 8080`
   - The service will be configured via environment variables:
     - `API_KEY` – production API key.
     - `DATABASE_URL` – connection string for the managed Postgres instance.
     - Optionally `CORS_ORIGINS` and other config values as needed.

2. **Postgres Hosting on Railway**

   - Use **Railway’s managed Postgres template** instead of running Postgres in a container on Railway.
   - The API’s `DATABASE_URL` will point to the managed Postgres instance provided by Railway.
   - Local development will continue to use Docker Compose (or SQLite) as currently documented, but production will rely on managed Postgres.

## Consequences

- **Pros**
  - **Simpler deployment pipeline**: No need to maintain or publish Docker images for the API on Railway. Git push triggers build-from-source deployments.
  - **Lower ops overhead**: Railway manages the base image, system packages, and runtime environment for the API service.
  - **Managed database benefits**: Backups, monitoring, and scaling for Postgres are handled by Railway, reducing operational complexity.
  - **Faster iteration**: Changes to the FastAPI code only require a git push; no container build/release choreography is needed.
  - **Clear separation of environments**: Local can continue to use Docker Compose, while production uses Railway-managed services.

- **Cons / Tradeoffs**
  - **Less control over runtime image**: We rely on Railway’s Python runtime rather than a fully custom Docker image. If we later need unusual system-level dependencies, we may have to reintroduce Docker for the API.
  - **Platform coupling**: The deployment setup becomes more Railway-specific (build-from-source assumptions, managed DB URLs), which may require some rework if migrating to another platform.
  - **Different dev vs prod topology**: Locally we may use Docker Compose or SQLite, while production uses managed Postgres. This is acceptable but should be documented clearly.

- **Future Options**
  - If requirements grow (complex system dependencies, multiple processes, or need for strict container parity across environments), we can introduce a Docker-based deployment for the API while keeping the managed Postgres.
  - If we need multi-region, cross-platform hosting later, we can revisit this ADR and potentially supersede it with a container-centric deployment strategy.
