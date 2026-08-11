import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Float, cast, desc, func
from sqlalchemy.orm import Session, selectinload

from app.core.deps import WorkspaceContext, require_viewer
from app.db.session import get_db
from app.models.asset import Asset
from app.models.tag import Tag
from app.schemas.asset import AssetSearchResult
from app.schemas.common import Page

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=Page[AssetSearchResult])
def search_assets(
    q: str | None = Query(default=None, min_length=1, max_length=200),
    folder_id: uuid.UUID | None = Query(default=None),
    content_type: str | None = Query(default=None),
    tag: list[str] = Query(default=[]),
    sort: Literal["relevance", "newest", "oldest", "name"] = Query(default="relevance"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    ctx: WorkspaceContext = Depends(require_viewer),
    db: Session = Depends(get_db),
) -> Page[AssetSearchResult]:
    """Full-text search over asset filename/original filename/description.

    Uses PostgreSQL's native `tsvector`/`tsquery` machinery (see the
    generated `search_vector` column on `Asset`) with `websearch_to_tsquery`
    for forgiving, Google-style query parsing, and `ts_rank_cd` for
    relevance ranking. Falls back to recency ordering when no query text is
    supplied (i.e. this endpoint doubles as a filtered browse view).
    """
    query = db.query(Asset).options(selectinload(Asset.tags)).filter(
        Asset.workspace_id == ctx.workspace_id
    )

    rank_expr = None
    if q:
        ts_query = func.websearch_to_tsquery("english", q)
        query = query.filter(Asset.search_vector.op("@@")(ts_query))
        rank_expr = cast(func.ts_rank_cd(Asset.search_vector, ts_query), Float)

    if folder_id is not None:
        query = query.filter(Asset.folder_id == folder_id)
    if content_type is not None:
        query = query.filter(Asset.content_type.like(f"{content_type}%"))
    if tag:
        query = query.join(Asset.tags).filter(Tag.name.in_(tag)).distinct()

    total = query.count()

    if sort == "relevance" and rank_expr is not None:
        query = query.order_by(desc(rank_expr))
    elif sort == "newest":
        query = query.order_by(desc(Asset.created_at))
    elif sort == "oldest":
        query = query.order_by(Asset.created_at.asc())
    elif sort == "name":
        query = query.order_by(Asset.filename.asc())
    else:
        query = query.order_by(desc(Asset.created_at))

    if rank_expr is not None:
        query = query.add_columns(rank_expr.label("rank"))
        rows = query.offset((page - 1) * page_size).limit(page_size).all()
        items = []
        for asset, rank in rows:
            result = AssetSearchResult.model_validate(asset)
            result.rank = float(rank) if rank is not None else None
            items.append(result)
    else:
        rows = query.offset((page - 1) * page_size).limit(page_size).all()
        items = [AssetSearchResult.model_validate(asset) for asset in rows]

    return Page.create(items=items, total=total, page=page, page_size=page_size)
