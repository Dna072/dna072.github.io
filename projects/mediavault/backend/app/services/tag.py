"""Tag management."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.tag import Tag
from app.repositories.tag import TagRepository


class TagService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tags = TagRepository(db)

    def list(self, workspace_id: uuid.UUID) -> list[Tag]:
        return self.tags.list_for_workspace(workspace_id)

    def create(self, workspace_id: uuid.UUID, name: str, color: str) -> Tag:
        name = name.strip()
        if self.tags.get_by_name(workspace_id, name):
            raise ConflictError("A tag with this name already exists.")
        return self.tags.add(Tag(workspace_id=workspace_id, name=name, color=color))

    def get_or_create(self, workspace_id: uuid.UUID, name: str, color: str = "#0f766e") -> Tag:
        existing = self.tags.get_by_name(workspace_id, name.strip())
        return existing or self.create(workspace_id, name, color)

    def get(self, workspace_id: uuid.UUID, tag_id: uuid.UUID) -> Tag:
        tag = self.tags.get_scoped(workspace_id, tag_id)
        if tag is None:
            raise NotFoundError("Tag not found.")
        return tag

    def update(self, tag: Tag, name: str | None, color: str | None) -> Tag:
        if name is not None:
            existing = self.tags.get_by_name(tag.workspace_id, name.strip())
            if existing and existing.id != tag.id:
                raise ConflictError("A tag with this name already exists.")
            tag.name = name.strip()
        if color is not None:
            tag.color = color
        self.db.flush()
        return tag

    def delete(self, tag: Tag) -> None:
        self.tags.delete(tag)
