# Tech Debt

- Auth hardening: replace X-API-Key with OAuth/JWT, per-user auth and RBAC.
- CORS tightening: restrict to specific extension origins in production.
- DB migrations: add Alembic and versioned migrations (currently using create_all).
- Observability: add request tracing and centralized log aggregation.
- Retry/queue: add durable queue for retries of failed API writes.
- Admin UI: build simple R/W console for entries and users.
