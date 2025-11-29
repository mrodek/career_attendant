from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    api_key: str = os.getenv("API_KEY", "dev_api_key")
    # Prefer Railway's PORT env var, fall back to APP_PORT, then 8080
    app_port: int = int(os.getenv("PORT", os.getenv("APP_PORT", 8080)))
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://jobaid:jobaidpass@db:5432/jobaid")

    class Config:
        env_file = ".env"

def get_cors_origins(settings: Settings) -> List[str]:
    origins = settings.cors_origins
    if origins == "*":
        return ["*"]
    return [o.strip() for o in origins.split(",") if o.strip()]
