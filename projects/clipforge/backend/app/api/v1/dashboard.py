from __future__ import annotations

from sqlalchemy import func, select

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.models.project import Project
from app.models.video import Video
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.dashboard import DashboardStats, StatusCount
from app.schemas.video import VideoListItem
from app.services.video_service import VideoService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(current_user: CurrentUser, db: DbSession) -> DashboardStats:
    # Videos visible to the current user (via workspace membership).
    scoped = (
        select(Video)
        .join(Project, Project.id == Video.project_id)
        .join(Workspace, Workspace.id == Project.workspace_id)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == current_user.id)
        .subquery()
    )

    total_videos = db.scalar(select(func.count()).select_from(scoped)) or 0
    total_duration = db.scalar(select(func.coalesce(func.sum(scoped.c.duration_seconds), 0.0))) or 0.0
    total_storage = db.scalar(select(func.coalesce(func.sum(scoped.c.size_bytes), 0))) or 0

    total_projects = db.scalar(
        select(func.count(func.distinct(Project.id)))
        .select_from(Project)
        .join(Workspace, Workspace.id == Project.workspace_id)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == current_user.id)
    ) or 0

    breakdown_rows = db.execute(
        select(scoped.c.status, func.count()).group_by(scoped.c.status)
    ).all()
    status_breakdown = [
        StatusCount(status=str(row[0].value if hasattr(row[0], "value") else row[0]), count=row[1])
        for row in breakdown_rows
    ]

    recent = VideoService(db).videos.recent_for_user(current_user.id, limit=6)

    return DashboardStats(
        total_videos=total_videos,
        total_projects=total_projects,
        total_duration_seconds=float(total_duration),
        total_storage_bytes=int(total_storage),
        status_breakdown=status_breakdown,
        recent_videos=[VideoListItem.model_validate(v) for v in recent],
    )
