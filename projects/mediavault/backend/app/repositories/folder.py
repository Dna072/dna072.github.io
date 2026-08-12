"""Folder repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from app.models.asset import Asset
from app.models.folder import Folder
from app.repositories.base import BaseRepository


class FolderRepository(BaseRepository[Folder]):
    model = Folder

    def list_for_workspace(self, workspace_id: uuid.UUID) -> list[Folder]:
        stmt = (
            select(Folder)
            .where(Folder.workspace_id == workspace_id)
            .order_by(Folder.path, Folder.name)
        )
        return list(self.db.execute(stmt).scalars())

    def get_scoped(self, workspace_id: uuid.UUID, folder_id: uuid.UUID) -> Folder | None:
        stmt = select(Folder).where(
            Folder.id == folder_id, Folder.workspace_id == workspace_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def sibling_exists(
        self, workspace_id: uuid.UUID, parent_id: uuid.UUID | None, name: str
    ) -> bool:
        stmt = select(func.count()).select_from(Folder).where(
            Folder.workspace_id == workspace_id,
            Folder.parent_id.is_(parent_id) if parent_id is None else Folder.parent_id == parent_id,
            func.lower(Folder.name) == name.lower(),
        )
        return self.db.execute(stmt).scalar_one() > 0

    def asset_counts(self, workspace_id: uuid.UUID) -> dict[uuid.UUID, int]:
        stmt = (
            select(Asset.folder_id, func.count())
            .where(Asset.workspace_id == workspace_id)
            .group_by(Asset.folder_id)
        )
        return {row[0]: row[1] for row in self.db.execute(stmt).all() if row[0] is not None}
