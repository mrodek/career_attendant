from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import Settings, get_cors_origins
from .logger import logger
from .routers import entries, auth, auth_page, analyze, extract
from .auth.middleware import AuthMiddleware
from .startup import init_db

settings = Settings()

app = FastAPI(title="JobAid API", version="0.1.0")

# CORS configuration
if settings.cors_origins == "*":
    allowed_origins = ["*"]
else:
    # Start with configured CORS origins (comma-separated)
    allowed_origins = get_cors_origins(settings)
    # Add frontend URL if not already included
    if settings.frontend_url and settings.frontend_url not in allowed_origins:
        allowed_origins.append(settings.frontend_url)
    # Add extension ID if configured
    if settings.extension_id:
        extension_origin = f"chrome-extension://{settings.extension_id}"
        if extension_origin not in allowed_origins:
            allowed_origins.append(extension_origin)

logger.info(f"CORS configuration: cors_origins='{settings.cors_origins}', allowed_origins={allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=settings.cors_origins != "*",  # Can't use credentials with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.middleware("http")(AuthMiddleware())

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    import os
    logger.info("Application starting up...")
    
    # Only drop tables if explicitly enabled (dev only!)
    drop_all = os.getenv("DROP_ALL_TABLES", "false").lower() == "true"
    init_db(drop_all=drop_all)
    
    logger.info("Application startup complete")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "dev_mode": settings.dev_mode,
        "clerk_frontend_api": "https://apparent-javelin-61.clerk.accounts.dev" if settings.clerk_jwks_url else None
    }

# Include routers
app.include_router(auth.router)
app.include_router(auth_page.router)
app.include_router(entries.router)
app.include_router(analyze.router)
app.include_router(extract.router)
