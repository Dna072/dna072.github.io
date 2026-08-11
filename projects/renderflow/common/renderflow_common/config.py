from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration, shared by the API and worker processes.

    Values are read from environment variables (see `.env.example`). Both
    processes construct this the same way so they always agree on the
    database DSN, queue keys and timing knobs.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres
    postgres_user: str = "renderflow"
    postgres_password: str = "renderflow_dev_password"
    postgres_db: str = "renderflow"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    database_url: str | None = None

    # Redis
    redis_url: str = "redis://redis:6379/0"
    queue_key: str = "renderflow:queue"
    delayed_queue_key: str = "renderflow:delayed"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    log_level: str = "INFO"
    scheduler_interval_seconds: float = 5
    heartbeat_timeout_seconds: float = 45

    # Worker
    worker_concurrency: int = 1
    worker_poll_timeout_seconds: int = 5
    heartbeat_interval_seconds: float = 10
    job_max_retries: int = 3
    retry_backoff_base_seconds: float = 10
    media_storage_path: str = "/data/media"
    force_mock_ffmpeg: bool = False

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
