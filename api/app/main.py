from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import Settings, get_cors_origins
from .db import Base, engine
from .logger import logger
from .routers import entries

settings = Settings()

app = FastAPI(title="JobAid API", version="0.1.0")

# CORS
origins = get_cors_origins(settings)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
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
