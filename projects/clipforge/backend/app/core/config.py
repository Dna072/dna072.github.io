"""Application configuration loaded from environment variables.

All secrets and environment-specific values are sourced from env vars so the same
image runs unchanged across local, CI, and cloud. See ``.env.example`` for the
full list.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "ClipForge API"
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    api_v1_prefix: str = "/api/v1"

    # --- Security ---
    secret_key: str = Field(default="dev-insecure-change-me")
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    jwt_algorithm: str = "HS256"

    # --- Database ---
    database_url: str = Field(
        default="postgresql+psycopg://clipforge:clipforge@localhost:5432/clipforge"
    )

    # --- Redis / queue ---
    redis_url: str = Field(default="redis://localhost:6379/0")
    processing_queue: str = "clipforge:jobs"

    # --- Storage ---
    storage_dir: str = Field(default="./storage")
    max_upload_bytes: int = Field(default=524_288_000)  # 500 MB
    allowed_video_extensions: list[str] = Field(
        default=["mp4", "mov", "mkv", "webm", "avi", "m4v"]
    )
    allowed_video_mime_types: list[str] = Field(
        default=[
            "video/mp4",
            "video/quicktime",
            "video/x-matroska",
            "video/webm",
            "video/x-msvideo",
            "video/x-m4v",
        ]
    )

    # --- AI ---
    ai_provider: str = Field(default="mock")  # "mock" | "openai"
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")

    # --- CORS ---
    cors_origins: list[str] = Field(default=["http://localhost:5173", "http://localhost:3000"])

    # --- Rate limiting ---
    rate_limit_default: str = Field(default="120/minute")
    rate_limit_auth: str = Field(default="10/minute")

    # --- Worker ---
    worker_poll_timeout: int = 5

    @field_validator(
        "allowed_video_extensions",
        "allowed_video_mime_types",
        "cors_origins",
        mode="before",
    )
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Allow comma-separated env strings for list fields."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def use_openai(self) -> bool:
        return self.ai_provider.lower() == "openai" and bool(self.openai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
