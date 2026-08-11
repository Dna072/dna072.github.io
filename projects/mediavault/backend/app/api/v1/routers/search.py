"""Full-text search endpoint with facets (nested under a workspace)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import DbSession, Pagination, WorkspaceCtx
from app.models.enums import AssetKind
from app.repositories.asset import AssetFilter
from app.schemas.asset import AssetRead
from app.schemas.common import Page
from app.schemas.search import SearchFacets, SearchResult
from app.services.search import SearchService

router = APIRouter(prefix="/workspaces/{workspace_id}/search", tags=["search"])


@router.get("", response_model=SearchResult)
def search_assets(
    ctx: WorkspaceCtx,
    db: DbSession,
    pagination: Pagination,
    q: Annotated[str, Query(min_length=1, description="Full-text query")],
    kind: Annotated[AssetKind | None, Query()] = None,
    tag_ids: Annotated[list[uuid.UUID] | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "relevance",
    sort_dir: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
) -> SearchResult:
    f = AssetFilter(
        workspace_id=ctx.workspace.id,
        kind=kind,
        tag_ids=tag_ids or [],
        query=q,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    items, total, facets = SearchService(db).search(
        f, offset=pagination.offset, limit=pagination.page_size
    )
    page = Page[AssetRead].build(
        [AssetRead.model_validate(a) for a in items],
        total,
        pagination.page,
        pagination.page_size,
    )
    return SearchResult(query=q, results=page, facets=SearchFacets(kinds=facets))
