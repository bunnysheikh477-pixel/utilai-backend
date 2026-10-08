from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "ToolForge"
    APP_ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "toolforge"
    USE_MEMORY_DB: bool = False

    JWT_SECRET: str = "change-me"
    JWT_REFRESH_SECRET: str = "change-me-refresh"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    REDIS_URL: str = "redis://localhost:6379/1"

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8001"

    STORAGE_DIR: str = "./storage"
    FILE_RETENTION_HOURS: int = 1
    MAX_UPLOAD_MB_FREE: int = 10
    MAX_UPLOAD_MB_PRO: int = 50
    ANON_DAILY_LIMIT: int = 10

    SUPERADMIN_EMAIL: str = "admin@toolforge.com"
    SUPERADMIN_PASSWORD: str = "ChangeMe123!"

    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    API_V1_PREFIX: str = "/api/v1"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
