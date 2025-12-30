from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    api_key: str = os.getenv("API_KEY", "dev_api_key")
    # Prefer Railway's PORT env var, fall back to APP_PORT, then 8080
    app_port: int = int(os.getenv("PORT", os.getenv("APP_PORT", 8080)))
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://jobaid:jobaidpass@db:5432/jobaid")
    
    # Development mode (set to "true" to bypass authentication)
    dev_mode: bool = os.getenv("DEV_MODE", "false").lower() == "true"
    
    # Clerk authentication
    clerk_secret_key: str = os.getenv("CLERK_SECRET_KEY", "")
    clerk_publishable_key: str = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "")
    clerk_jwks_url: str = os.getenv("CLERK_JWKS_URL", "")
    
    # Frontend and extension configuration
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    extension_id: str = os.getenv("EXTENSION_ID", "")

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra env vars

def get_cors_origins(settings: Settings) -> List[str]:
    origins = settings.cors_origins
    if origins == "*":
        return ["*"]
    return [o.strip() for o in origins.split(",") if o.strip()]
