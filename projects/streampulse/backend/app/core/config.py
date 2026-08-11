"""Application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "StreamPulse API"
    environment: str = "development"

    database_url: str = "postgresql+psycopg2://streampulse:streampulse@localhost:5432/streampulse"

    jwt_secret_key: str = "change-me-in-production-please"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    seed_videos: int = 40
    seed_days: int = 120
    seed_min_daily_events_per_video: int = 5
    seed_max_daily_events_per_video: int = 400
    seed_random_seed: int = 42

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
