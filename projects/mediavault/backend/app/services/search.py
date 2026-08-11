"""Search service producing paged results plus facets."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.asset import AssetFilter, AssetRepository


class SearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.assets = AssetRepository(db)

    def search(self, f: AssetFilter, *, offset: int, limit: int):
        items, total = self.assets.search(f, offset=offset, limit=limit)
        facets = self.assets.kind_facets(f)
        return items, total, facets
