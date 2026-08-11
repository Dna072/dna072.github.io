"""Application configuration loaded from environment variables.

Uses pydantic-settings so configuration is validated at startup and typed
throughout the codebase. Sensible defaults are provided so the application
boots in demo mode without any external services or secrets.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, List, Tuple, Type

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import EnvSettingsSource, PydanticBaseSettingsSource

# Fields that accept a comma-separated string from the environment. We disable
# pydantic-settings' default JSON decoding for these so plain CSV values work.
_CSV_FIELDS = {"cors_origins", "allowed_video_extensions", "allowed_video_mime_types"}


class _CsvEnvSource(EnvSettingsSource):
    """Env source that returns raw strings for CSV list fields (no JSON decode)."""

    def prepare_field_value(
        self, field_name: str, field: Any, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name in _CSV_FIELDS and isinstance(value, str):
            return value
        return super().prepare_field_value(
            field_name, field, value, value_is_complex
        )


class Settings(BaseSettings):
    """Typed application settings.

    All values can be overridden through environment variables (or a local
    ``.env`` file). Defaults are safe for local/demo usage.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App -------------------------------------------------------------
    app_name: str = "ClipForge"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    api_v1_prefix: str = "/api/v1"

    # --- Security --------------------------------------------------------
    # NOTE: override JWT_SECRET_KEY in any real deployment.
    jwt_secret_key: str = Field(default="dev-insecure-change-me")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12

    # --- Database --------------------------------------------------------
    database_url: str = Field(
        default="sqlite:///./clipforge.db",
        description="SQLAlchemy database URL",
    )

    # --- Redis / queue ---------------------------------------------------
    redis_url: str = Field(default="redis://localhost:6379/0")
    job_queue_name: str = "clipforge:jobs"

    # --- Storage ---------------------------------------------------------
    storage_dir: str = Field(default="./storage")
    max_upload_bytes: int = Field(default=500 * 1024 * 1024)  # 500 MB
    allowed_video_extensions: List[str] = Field(
        default_factory=lambda: ["mp4", "mov", "mkv", "webm", "avi", "m4v"]
    )
    allowed_video_mime_types: List[str] = Field(
        default_factory=lambda: [
            "video/mp4",
            "video/quicktime",
            "video/x-matroska",
            "video/webm",
            "video/x-msvideo",
            "video/x-m4v",
            "application/octet-stream",
        ]
    )

    # --- AI --------------------------------------------------------------
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")
    ai_provider: str = Field(default="auto")  # auto | mock | openai

    # --- CORS ------------------------------------------------------------
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )

    # --- Logging ---------------------------------------------------------
    log_level: str = Field(default="INFO")
    log_json: bool = Field(default=True)

    @field_validator(
        "allowed_video_extensions",
        "allowed_video_mime_types",
        "cors_origins",
        mode="before",
    )
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Allow comma-separated env values for list fields."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            _CsvEnvSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    def resolved_ai_provider(self) -> str:
        """Return the provider that should actually be used.

        In ``auto`` mode we use OpenAI when an API key is present, otherwise we
        fall back to the deterministic mock provider so demos work offline.
        """
        if self.ai_provider != "auto":
            return self.ai_provider
        return "openai" if self.openai_api_key else "mock"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
