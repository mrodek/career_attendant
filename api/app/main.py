import os
import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import Settings, get_cors_origins
from .logger import logger
from .routers import entries, auth, auth_page, analyze, extract, resumes
from .auth.middleware import AuthMiddleware
from .startup import init_db

# Configure more detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)

settings = Settings()
logger.info(f"Starting application with PORT={settings.app_port}")
logger.info(f"Environment variables: DATABASE_URL={'SET' if settings.database_url else 'NOT SET'}, ENCRYPTION_MASTER_KEY={'SET' if os.getenv('ENCRYPTION_MASTER_KEY') else 'NOT SET'}")

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
    logger.info("=== APPLICATION STARTUP BEGIN ===")
    try:
        init_db(drop_all=settings.dev_mode)
        logger.info("✅ Database initialization completed")
        
        logger.info("✅ Application startup complete")
        logger.info(f"✅ Server running on http://0.0.0.0:{settings.app_port}")
        logger.info("=== APPLICATION STARTUP COMPLETE ===")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=== APPLICATION SHUTDOWN BEGIN ===")
    try:
        logger.info("🔄 Cleaning up resources...")
        logger.info("✅ Application shutdown complete")
        logger.info("=== APPLICATION SHUTDOWN COMPLETE ===")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

@app.get("/health")
def health():
    logger.info("🏥 Health check requested")
    response = {
        "status": "ok",
        "dev_mode": settings.dev_mode,
        "clerk_frontend_api": "https://apparent-javelin-61.clerk.accounts.dev" if settings.clerk_jwks_url else None
    }
    logger.info(f"🏥 Health check response: {response}")
    return response

# Include routers
app.include_router(auth.router)
app.include_router(auth_page.router)
app.include_router(entries.router)
app.include_router(analyze.router)
app.include_router(extract.router)
app.include_router(resumes.router)
