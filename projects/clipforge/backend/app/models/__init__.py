"""ORM models package.

Importing this package registers all models on the shared ``Base.metadata``
so Alembic autogeneration and ``create_all`` see every table.
"""

from app.models.base import Base
from app.models.job import ProcessingJob
from app.models.user import User
from app.models.video import Video
from app.models.workspace import Workspace

__all__ = ["Base", "User", "Workspace", "Video", "ProcessingJob"]
