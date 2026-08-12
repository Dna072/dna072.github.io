"""Asset repository: filtering, sorting, pagination and full-text search."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.asset import Asset, AssetTag
from app.models.enums import AssetKind
from app.repositories.base import BaseRepository

SORTABLE_FIELDS = {
    "created_at": Asset.created_at,
    "updated_at": Asset.updated_at,
    "name": Asset.name,
    "size_bytes": Asset.size_bytes,
}


@dataclass
class AssetFilter:
    workspace_id: uuid.UUID
    folder_id: uuid.UUID | None = None
    include_subfolders: bool = False
    subfolder_ids: list[uuid.UUID] = field(default_factory=list)
    kind: AssetKind | None = None
    tag_ids: list[uuid.UUID] = field(default_factory=list)
    query: str | None = None
    sort_by: str = "created_at"
    sort_dir: str = "desc"


class AssetRepository(BaseRepository[Asset]):
    model = Asset

    def get_scoped(self, workspace_id: uuid.UUID, asset_id: uuid.UUID) -> Asset | None:
        stmt = (
            select(Asset)
            .options(selectinload(Asset.tags))
            .where(Asset.id == asset_id, Asset.workspace_id == workspace_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    # --- Query building -----------------------------------------------------
    def _base_query(self, f: AssetFilter) -> Select:
        stmt = select(Asset).where(Asset.workspace_id == f.workspace_id)

        if f.folder_id is not None:
            if f.include_subfolders and f.subfolder_ids:
                stmt = stmt.where(Asset.folder_id.in_([f.folder_id, *f.subfolder_ids]))
            else:
                stmt = stmt.where(Asset.folder_id == f.folder_id)

        if f.kind is not None:
            stmt = stmt.where(Asset.kind == f.kind)

        if f.tag_ids:
            # Require the asset to carry every requested tag (AND semantics).
            for tag_id in f.tag_ids:
                exists_subq = (
                    select(AssetTag.asset_id)
                    .where(AssetTag.asset_id == Asset.id, AssetTag.tag_id == tag_id)
                    .exists()
                )
                stmt = stmt.where(exists_subq)

        if f.query:
            stmt = self._apply_search(stmt, f.query)

        return stmt

    def _apply_search(self, stmt: Select, query: str) -> Select:
        """Apply full-text search on PostgreSQL, ILIKE fallback elsewhere."""
        if settings.is_postgres:
            ts_query = func.websearch_to_tsquery("english", query)
            return stmt.where(Asset.search_vector.op("@@")(ts_query))

        like = f"%{query.lower()}%"
        return stmt.where(
            or_(
                func.lower(Asset.name).like(like),
                func.lower(Asset.description).like(like),
                func.lower(Asset.original_filename).like(like),
            )
        )

    def _apply_sort(self, stmt: Select, f: AssetFilter) -> Select:
        # Relevance ranking when a text query is present on PostgreSQL.
        if f.query and settings.is_postgres and f.sort_by == "relevance":
            rank = func.ts_rank(Asset.search_vector, func.websearch_to_tsquery("english", f.query))
            return stmt.order_by(rank.desc(), Asset.created_at.desc())

        column = SORTABLE_FIELDS.get(f.sort_by, Asset.created_at)
        ordering = column.desc() if f.sort_dir == "desc" else column.asc()
        return stmt.order_by(ordering, Asset.id.desc())

    def search(self, f: AssetFilter, *, offset: int, limit: int) -> tuple[list[Asset], int]:
        base = self._base_query(f)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = self._apply_sort(base, f).options(selectinload(Asset.tags)).offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().unique())
        return items, total

    def kind_facets(self, f: AssetFilter) -> dict[str, int]:
        base = self._base_query(f).subquery()
        stmt = select(base.c.kind, func.count()).group_by(base.c.kind)
        return {str(row[0].value if hasattr(row[0], "value") else row[0]): row[1] for row in self.db.execute(stmt).all()}
