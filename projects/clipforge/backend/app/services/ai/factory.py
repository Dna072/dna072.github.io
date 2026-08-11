"""AI provider factory / selection logic."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger
from app.services.ai.base import AIProvider
from app.services.ai.mock_provider import MockAIProvider

logger = get_logger("clipforge.ai")


@lru_cache
def get_ai_provider() -> AIProvider:
    """Return the configured AI provider (cached process-wide)."""
    choice = settings.resolved_ai_provider()
    if choice == "openai":
        from app.services.ai.openai_provider import OpenAIProvider  # lazy import

        logger.info("ai_provider_selected", extra={"provider": "openai"})
        return OpenAIProvider()
    logger.info("ai_provider_selected", extra={"provider": "mock"})
    return MockAIProvider()
