"""Portable column types.

``JSONType`` stores JSON as native ``JSONB`` on PostgreSQL and falls back to the
generic ``JSON`` type elsewhere (e.g. SQLite for local/dev/test).
"""

from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

JSONType = JSON().with_variant(JSONB, "postgresql")
