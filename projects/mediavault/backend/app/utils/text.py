"""Small text helpers (slugs, tokens)."""

from __future__ import annotations

import re
import secrets
import unicodedata


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "workspace"


def unique_slug(base: str, exists) -> str:
    """Return a slug derived from ``base`` that passes ``exists(slug) is False``."""
    slug = slugify(base)
    candidate = slug
    counter = 2
    while exists(candidate):
        candidate = f"{slug}-{counter}"
        counter += 1
    return candidate


def random_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)
