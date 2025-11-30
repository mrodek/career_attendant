from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import Settings, get_cors_origins
from .db import Base, engine
from .logger import logger
from .routers import entries
from . import models  # Import models so they're registered with Base

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

# Create tables (replace with Alembic later)
Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(entries.router)
