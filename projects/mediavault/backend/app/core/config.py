"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "MediaVault API"
    ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "change-me-in-production-please-use-a-random-64-char-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 14  # 14 days
    SIGNED_URL_EXPIRE_SECONDS: int = 600
    SHARE_LINK_DEFAULT_EXPIRE_HOURS: int = 24 * 7

    # Database
    DATABASE_URL: str = "postgresql+psycopg://mediavault:mediavault@localhost:5432/mediavault"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Storage (local filesystem abstraction; swappable for S3 later)
    STORAGE_BACKEND: str = "local"
    STORAGE_ROOT: str = str(Path(__file__).resolve().parents[2] / "storage")
    MAX_UPLOAD_SIZE_MB: int = 512

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
