"""Application configuration loaded from environment variables."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings.

    Values are read from the environment (and an optional ``.env`` file). All
    secrets must be provided via the environment in real deployments; the
    defaults here only exist to make local development and tests frictionless.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---------------------------------------------------------
    PROJECT_NAME: str = "MediaVault"
    ENVIRONMENT: Literal["local", "test", "staging", "production"] = "local"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    # --- Security ------------------------------------------------------------
    SECRET_KEY: str = Field(
        default="change-me-in-production-a-very-long-random-string",
        description="Symmetric key used to sign JWT access/refresh tokens.",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    # Key used to sign short-lived asset download URLs (HMAC).
    SIGNED_URL_SECRET: str = "change-me-signed-url-secret"
    SIGNED_URL_EXPIRE_SECONDS: int = 900

    # --- CORS ----------------------------------------------------------------
    # NoDecode: pydantic-settings otherwise JSON-decodes list env vars and
    # crashes on CSV / empty values common in docker-compose/.env files.
    BACKEND_CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ]
    )

    # --- Database ------------------------------------------------------------
    DATABASE_URL: str = "postgresql+psycopg://mediavault:mediavault@localhost:5432/mediavault"

    # --- Redis (optional; rate limiting / caching) ---------------------------
    REDIS_URL: str | None = "redis://localhost:6379/0"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120

    # --- Storage -------------------------------------------------------------
    # "local" writes to STORAGE_LOCAL_DIR; "s3" uses an S3-compatible backend.
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    STORAGE_LOCAL_DIR: str = "/data/storage"
    S3_BUCKET: str | None = None
    S3_REGION: str | None = "us-east-1"
    S3_ENDPOINT_URL: str | None = None  # e.g. MinIO endpoint
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None

    # --- Uploads -------------------------------------------------------------
    MAX_UPLOAD_SIZE_MB: int = 512
    ALLOWED_UPLOAD_CONTENT_TYPES: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "video/mp4",
            "video/quicktime",
            "video/webm",
            "video/x-matroska",
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/gif",
            "application/pdf",
        ]
    )

    # --- Seed / bootstrap ----------------------------------------------------
    FIRST_SUPERUSER_EMAIL: str = "admin@mediavault.dev"
    FIRST_SUPERUSER_PASSWORD: str = "ChangeMe123!"

    @field_validator("BACKEND_CORS_ORIGINS", "ALLOWED_UPLOAD_CONTENT_TYPES", mode="before")
    @classmethod
    def _parse_string_list(cls, value: object) -> object:
        """Accept JSON arrays, CSV strings, or empty env values for list settings."""
        if value is None:
            return value
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if text.startswith("["):
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    # Fall through to CSV parsing for near-JSON mistakes.
                    pass
            return [item.strip() for item in text.split(",") if item.strip()]
        return value

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def is_postgres(self) -> bool:
        return "postgresql" in self.DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
