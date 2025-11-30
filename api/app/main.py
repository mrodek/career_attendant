from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import Settings, get_cors_origins
from .logger import logger
from .routers import entries
from .startup import init_db

settings = Settings()

app = FastAPI(title="JobAid API", version="0.1.0")

# CORS - Allow all origins including Chrome extensions
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",  # Allow all origins including chrome-extension://
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "ok"}

app.include_router(entries.router)
