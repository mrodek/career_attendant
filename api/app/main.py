from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import Settings, get_cors_origins
from .logger import logger
from .routers import entries, auth, auth_page
from .auth.middleware import AuthMiddleware
from .startup import init_db

settings = Settings()

app = FastAPI(title="JobAid API", version="0.1.0")

# CORS configuration
allowed_origins = [settings.frontend_url]
if settings.extension_id:
    allowed_origins.append(f"chrome-extension://{settings.extension_id}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if settings.cors_origins != "*" else ["*"],
    allow_origin_regex=r".*" if settings.cors_origins == "*" else None,
    allow_credentials=True,
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
