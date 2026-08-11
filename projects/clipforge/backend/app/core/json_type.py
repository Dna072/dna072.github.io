"""Portable JSON column type.

Uses PostgreSQL ``JSONB`` in production for indexed/binary JSON storage, and
falls back to the generic ``JSON`` type on other backends (e.g. SQLite in tests).
"""

from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

JSONType = JSON().with_variant(JSONB(), "postgresql")
