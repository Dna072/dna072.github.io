"""Dashboard aggregation service."""

from __future__ import annotations

from collections import Counter

from sqlalchemy.orm import Session

from app.models.enums import VideoStatus
from app.models.user import User
from app.repositories.job_repo import JobRepository
from app.repositories.video_repo import VideoRepository
from app.repositories.workspace_repo import WorkspaceRepository
from app.schemas.dashboard import DashboardStats, StatusBreakdown
from app.schemas.video import VideoPublic


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.videos = VideoRepository(db)
        self.workspaces = WorkspaceRepository(db)
        self.jobs = JobRepository(db)

    def stats(self, user: User) -> DashboardStats:
        all_videos = self.videos.all_for_owner(user.id)
        workspaces = self.workspaces.list_for_owner(user.id)

        breakdown = StatusBreakdown()
        total_duration = 0.0
        total_storage = 0
        tag_counter: Counter[str] = Counter()

        for video in all_videos:
            setattr(
                breakdown,
                video.status.value if isinstance(video.status, VideoStatus) else str(video.status),
                getattr(
                    breakdown,
                    video.status.value
                    if isinstance(video.status, VideoStatus)
                    else str(video.status),
                    0,
                )
                + 1,
            )
            total_duration += video.duration_seconds or 0.0
            total_storage += video.size_bytes or 0
            for tag in video.tags or []:
                tag_counter[tag] += 1

        recent = self.videos.recent_for_owner(user.id, limit=6)
        top_tags = [
            {"tag": tag, "count": count}
            for tag, count in tag_counter.most_common(8)
        ]

        return DashboardStats(
            total_videos=len(all_videos),
            total_workspaces=len(workspaces),
            total_duration_seconds=round(total_duration, 2),
            total_storage_bytes=total_storage,
            status_breakdown=breakdown,
            active_jobs=self.jobs.count_active_for_owner(user.id),
            recent_videos=[VideoPublic.model_validate(v) for v in recent],
            top_tags=top_tags,
        )
