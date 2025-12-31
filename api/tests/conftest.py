import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Set test environment BEFORE importing app modules
os.environ.setdefault("API_KEY", "dev_api_key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("DEV_MODE", "true")  # Bypass JWT auth in tests

# Ensure the 'app' package (api/app) is importable when running tests from api/
API_DIR = Path(__file__).resolve().parents[1]  # points to .../api
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.main import app  # noqa: E402
from app.db import Base  # noqa: E402
from app.db import get_db  # noqa: E402

# Create a dedicated SQLite engine for tests that shares the same in-memory DB
engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables for the in-memory database
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override the dependency to use the SQLite session
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    return TestClient(app)
