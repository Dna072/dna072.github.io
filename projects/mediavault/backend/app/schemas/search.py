"""Search request/response schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.schemas.asset import AssetRead
from app.schemas.common import Page


class SearchResult(BaseModel):
    query: str
    results: Page[AssetRead]
    facets: SearchFacets


class SearchFacets(BaseModel):
    kinds: dict[str, int] = {}
    tags: dict[str, int] = {}


class TagFacet(BaseModel):
    id: uuid.UUID
    name: str
    count: int


SearchResult.model_rebuild()
