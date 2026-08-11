"""Application configuration loaded from environment variables.

Settings are intentionally environment-driven so the same image can run as the
API or as a worker in Docker Compose, Kubernetes, or a local dev shell.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the RenderFlow platform."""

    model_config = SettingsConfigDict(
        env_prefix="RENDERFLOW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- General -----------------------------------------------------------
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    service_name: str = Field(default="renderflow-api")

    # --- Database ----------------------------------------------------------
    # Defaults to a local SQLite file so the API and tests run with zero infra.
    # In Compose/K8s this is overridden with a PostgreSQL DSN.
    database_url: str = Field(default="sqlite:///./renderflow.db")

    # --- Queue -------------------------------------------------------------
    # When empty, an in-process queue is used (handy for tests / single-node
    # demos). In production a Redis URL wires the API and workers together.
    redis_url: str = Field(default="")
    queue_key: str = Field(default="renderflow:queue")

    # --- Object storage ----------------------------------------------------
    storage_backend: str = Field(default="local")  # "local" | "s3"
    storage_local_dir: str = Field(default="./storage")
    s3_bucket: str = Field(default="")
    s3_endpoint_url: str = Field(default="")
    s3_region: str = Field(default="us-east-1")

    # --- Job/retry policy --------------------------------------------------
    default_max_retries: int = Field(default=3)
    retry_backoff_base_seconds: float = Field(default=2.0)
    retry_backoff_max_seconds: float = Field(default=300.0)
    retry_backoff_jitter_seconds: float = Field(default=1.0)

    # --- Worker ------------------------------------------------------------
    worker_poll_interval_seconds: float = Field(default=1.0)
    worker_heartbeat_interval_seconds: float = Field(default=5.0)
    # Workers are considered stale (offline) if no heartbeat within this window.
    worker_stale_after_seconds: float = Field(default=30.0)
    # Jobs stuck RUNNING past this many seconds are reaped and retried.
    job_lease_seconds: float = Field(default=600.0)

    # --- Processing --------------------------------------------------------
    # Force mock processing even when ffmpeg is present (useful in CI).
    force_mock_processing: bool = Field(default=False)
    ffmpeg_binary: str = Field(default="ffmpeg")
    ffprobe_binary: str = Field(default="ffprobe")

    @property
    def is_testing(self) -> bool:
        return self.environment.lower() in {"test", "testing"}


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
