"""Video endpoints: upload, CRUD, search, and per-video job status."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.models.enums import VideoStatus
from app.schemas.common import Message, Page
from app.schemas.job import JobPublic
from app.schemas.video import (
    VideoDetail,
    VideoPublic,
    VideoUpdate,
    VideoUploadResponse,
)
from app.services.video_service import VideoService

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post(
    "/upload",
    response_model=VideoUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_video(
    current_user: CurrentUser,
    db: DbSession,
    workspace_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
    description: Annotated[str | None, Form()] = None,
) -> VideoUploadResponse:
    service = VideoService(db)
    video, job = service.create_from_upload(
        current_user,
        workspace_id,
        filename=file.filename or "upload.mp4",
        content_type=file.content_type or "application/octet-stream",
        file=file.file,
        declared_size=getattr(file, "size", None),
        title=title,
        description=description,
    )
    return VideoUploadResponse(
        video=VideoPublic.model_validate(video), job_id=job.id
    )


@router.get("", response_model=Page[VideoPublic])
def list_videos(
    current_user: CurrentUser,
    db: DbSession,
    q: Annotated[str | None, Query(description="Full-text query")] = None,
    workspace_id: str | None = None,
    status_filter: Annotated[VideoStatus | None, Query(alias="status")] = None,
    tag: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[VideoPublic]:
    items, total = VideoService(db).search(
        current_user,
        query=q,
        workspace_id=workspace_id,
        status=status_filter,
        tag=tag,
        limit=limit,
        offset=offset,
    )
    return Page[VideoPublic](
        items=[VideoPublic.model_validate(v) for v in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{video_id}", response_model=VideoDetail)
def get_video(
    video_id: str, current_user: CurrentUser, db: DbSession
) -> VideoDetail:
    video = VideoService(db).get(current_user, video_id)
    return VideoDetail.model_validate(video)


@router.get("/{video_id}/job", response_model=JobPublic)
def get_video_job(
    video_id: str, current_user: CurrentUser, db: DbSession
) -> JobPublic:
    service = VideoService(db)
    service.get(current_user, video_id)  # ownership check
    job = service.latest_job(video_id)
    if job is None:
        raise NotFoundError("No processing job for this video.")
    return JobPublic.model_validate(job)


@router.get("/{video_id}/thumbnail")
def get_video_thumbnail(
    video_id: str, current_user: CurrentUser, db: DbSession
):
    video = VideoService(db).get(current_user, video_id)
    if not video.thumbnail_path or not Path(video.thumbnail_path).exists():
        raise NotFoundError("Thumbnail not available yet.")
    return FileResponse(video.thumbnail_path)


@router.patch("/{video_id}", response_model=VideoDetail)
def update_video(
    video_id: str,
    payload: VideoUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> VideoDetail:
    video = VideoService(db).update(current_user, video_id, payload)
    return VideoDetail.model_validate(video)


@router.post("/{video_id}/reprocess", response_model=JobPublic)
def reprocess_video(
    video_id: str, current_user: CurrentUser, db: DbSession
) -> JobPublic:
    job = VideoService(db).reprocess(current_user, video_id)
    return JobPublic.model_validate(job)


@router.delete("/{video_id}", response_model=Message)
def delete_video(
    video_id: str, current_user: CurrentUser, db: DbSession
) -> Message:
    VideoService(db).delete(current_user, video_id)
    return Message(message="Video deleted.")
