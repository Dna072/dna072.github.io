from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, Query, Response, UploadFile, status

from app.core.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.models.video import VideoStatus
from app.schemas.common import Page
from app.schemas.job import JobRead
from app.schemas.video import VideoListItem, VideoRead, VideoUpdate
from app.services.video_service import VideoService

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("", response_model=VideoRead, status_code=status.HTTP_201_CREATED)
def upload_video(
    current_user: CurrentUser,
    db: DbSession,
    project_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
) -> VideoRead:
    """Upload a source video and enqueue it for asynchronous processing."""
    # Determine size without loading the whole file into memory.
    file.file.seek(0, 2)
    size_bytes = file.file.tell()
    file.file.seek(0)

    service = VideoService(db)
    video = service.create_video(
        project_id=project_id,
        user_id=current_user.id,
        filename=file.filename or "upload.mp4",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        stream=file.file,
        title=title,
    )
    return VideoRead.model_validate(video)


@router.get("", response_model=Page[VideoListItem])
def search_videos(
    current_user: CurrentUser,
    db: DbSession,
    q: Annotated[
        str | None, Query(description="Search over title/summary/transcript")
    ] = None,
    status_filter: Annotated[VideoStatus | None, Query(alias="status")] = None,
    project_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[VideoListItem]:
    service = VideoService(db)
    items, total = service.videos.search(
        current_user.id,
        query=q,
        status=status_filter,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return Page[VideoListItem](
        items=[VideoListItem.model_validate(v) for v in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{video_id}", response_model=VideoRead)
def get_video(video_id: str, current_user: CurrentUser, db: DbSession) -> VideoRead:
    video = VideoService(db).get_video(video_id, current_user.id)
    return VideoRead.model_validate(video)


@router.patch("/{video_id}", response_model=VideoRead)
def update_video(
    video_id: str, data: VideoUpdate, current_user: CurrentUser, db: DbSession
) -> VideoRead:
    video = VideoService(db).update_video(video_id, current_user.id, data)
    return VideoRead.model_validate(video)


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(video_id: str, current_user: CurrentUser, db: DbSession) -> Response:
    VideoService(db).delete_video(video_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{video_id}/status", response_model=JobRead)
def get_video_status(video_id: str, current_user: CurrentUser, db: DbSession) -> JobRead:
    job = VideoService(db).get_latest_job(video_id, current_user.id)
    if job is None:
        raise NotFoundError("No processing job found for this video")
    return JobRead.model_validate(job)


@router.post("/{video_id}/reprocess", response_model=JobRead, status_code=status.HTTP_202_ACCEPTED)
def reprocess_video(video_id: str, current_user: CurrentUser, db: DbSession) -> JobRead:
    job = VideoService(db).reprocess(video_id, current_user.id)
    return JobRead.model_validate(job)
