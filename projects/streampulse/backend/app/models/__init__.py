"""ORM models package.

Importing everything here ensures Alembic's ``target_metadata`` sees all tables.
"""

from app.models.analytics import (  # noqa: F401
    DeviceType,
    ImpressionEvent,
    Video,
    ViewEvent,
)
from app.models.user import User  # noqa: F401
