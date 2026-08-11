"""Exponential backoff with jitter for job retries."""

from __future__ import annotations

import random

from .config import Settings


def compute_backoff_seconds(
    attempt: int,
    settings: Settings,
    *,
    jitter: bool = True,
) -> float:
    """Return the delay before retry number ``attempt`` (1-based).

    Uses exponential growth ``base ** attempt`` capped at ``max`` with a small
    random jitter to avoid thundering-herd re-queues after a shared outage.
    """
    attempt = max(1, attempt)
    delay = settings.retry_backoff_base_seconds ** attempt
    delay = min(delay, settings.retry_backoff_max_seconds)
    if jitter and settings.retry_backoff_jitter_seconds > 0:
        delay += random.uniform(0, settings.retry_backoff_jitter_seconds)  # noqa: S311 - jitter, not crypto
    return round(delay, 3)
