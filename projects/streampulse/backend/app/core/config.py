"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    project_name: str = "StreamPulse"
    api_v1_prefix: str = "/api/v1"
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    log_json: bool = Field(default=True)

    # --- Database ---
    # Full SQLAlchemy URL. Compose supplies this; local dev can override.
    database_url: str = Field(
        default="postgresql+psycopg2://streampulse:streampulse@localhost:5432/streampulse"
    )
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # --- Auth ---
    secret_key: str = Field(default="change-me-in-production-please-32-chars-min")
    access_token_expire_minutes: int = 60 * 24
    jwt_algorithm: str = "HS256"

    # First user created by the seed script.
    seed_admin_email: str = "demo@streampulse.dev"
    seed_admin_password: str = "streampulse-demo"

    # --- CORS ---
    # Comma-separated list of allowed origins for the browser frontend.
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8080"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
