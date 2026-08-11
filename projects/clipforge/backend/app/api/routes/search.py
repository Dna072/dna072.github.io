"""Search endpoint (alias over video search with a search-centric response)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.models.enums import VideoStatus
from app.schemas.common import Page
from app.schemas.video import VideoPublic
from app.services.video_service import VideoService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=Page[VideoPublic])
def search(
    current_user: CurrentUser,
    db: DbSession,
    q: Annotated[str, Query(min_length=1, description="Search query")],
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
