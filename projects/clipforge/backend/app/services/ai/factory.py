from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger
from app.services.ai.base import AIProvider
from app.services.ai.mock import MockAIProvider

logger = get_logger(__name__)


def get_ai_provider() -> AIProvider:
    """Return the configured AI provider.

    Falls back to the mock provider whenever OpenAI is not fully configured, so
    the platform always has a working AI path (demo mode).
    """
    if settings.use_openai:
        try:
            from app.services.ai.openai_provider import OpenAIProvider

            return OpenAIProvider()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("openai_provider_init_failed", error=str(exc))
            return MockAIProvider()
    return MockAIProvider()
