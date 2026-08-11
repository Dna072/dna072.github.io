"""Small text helpers."""

from __future__ import annotations

import re
import unicodedata


def slugify(value: str) -> str:
    """Return a URL-safe slug for a human string."""
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    value = re.sub(r"[-\s]+", "-", value)
    return value or "workspace"


def title_from_filename(filename: str) -> str:
    """Derive a readable title from an uploaded filename."""
    stem = filename.rsplit("/", 1)[-1]
    stem = stem.rsplit(".", 1)[0]
    stem = re.sub(r"[_\-]+", " ", stem).strip()
    return stem.title() or "Untitled video"
