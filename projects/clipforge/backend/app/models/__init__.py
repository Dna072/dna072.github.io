"""SQLAlchemy ORM models.

Importing this package registers every model on the shared ``Base.metadata`` so
Alembic autogeneration and ``create_all`` (tests) see the full schema.
"""

from app.models.job import ProcessingJob
from app.models.project import Project
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.models.workspace import Workspace, WorkspaceMember

__all__ = [
    "User",
    "Workspace",
    "WorkspaceMember",
    "Project",
    "Video",
    "VideoStatus",
    "ProcessingJob",
]
