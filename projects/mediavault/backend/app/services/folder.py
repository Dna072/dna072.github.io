"""Folder hierarchy management with materialized paths."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.folder import Folder
from app.models.user import User
from app.repositories.folder import FolderRepository
from app.schemas.folder import Breadcrumb, FolderTree


class FolderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.folders = FolderRepository(db)

    def _resolve_path(self, workspace_id: uuid.UUID, parent_id: uuid.UUID | None, name: str) -> str:
        if parent_id is None:
            return f"/{name}"
        parent = self.folders.get_scoped(workspace_id, parent_id)
        if parent is None:
            raise NotFoundError("Parent folder not found.")
        return f"{parent.path.rstrip('/')}/{name}"

    def create(
        self, workspace_id: uuid.UUID, user: User, name: str, parent_id: uuid.UUID | None
    ) -> Folder:
        name = name.strip()
        if "/" in name:
            raise ValidationError("Folder name cannot contain '/'.")
        if self.folders.sibling_exists(workspace_id, parent_id, name):
            raise ConflictError("A folder with this name already exists here.")
        folder = Folder(
            workspace_id=workspace_id,
            parent_id=parent_id,
            name=name,
            path=self._resolve_path(workspace_id, parent_id, name),
            created_by=user.id,
        )
        return self.folders.add(folder)

    def get(self, workspace_id: uuid.UUID, folder_id: uuid.UUID) -> Folder:
        folder = self.folders.get_scoped(workspace_id, folder_id)
        if folder is None:
            raise NotFoundError("Folder not found.")
        return folder

    def list_tree(self, workspace_id: uuid.UUID) -> list[FolderTree]:
        folders = self.folders.list_for_workspace(workspace_id)
        counts = self.folders.asset_counts(workspace_id)
        nodes: dict[uuid.UUID, FolderTree] = {
            f.id: FolderTree.model_validate(f, from_attributes=True) for f in folders
        }
        for node in nodes.values():
            node.asset_count = counts.get(node.id, 0)
        roots: list[FolderTree] = []
        for folder in folders:
            node = nodes[folder.id]
            if folder.parent_id and folder.parent_id in nodes:
                nodes[folder.parent_id].children.append(node)
            else:
                roots.append(node)
        return roots

    def descendant_ids(self, workspace_id: uuid.UUID, folder_id: uuid.UUID) -> list[uuid.UUID]:
        """Return all descendant folder ids (using the materialized path prefix)."""
        root = self.get(workspace_id, folder_id)
        prefix = root.path.rstrip("/") + "/"
        return [
            f.id
            for f in self.folders.list_for_workspace(workspace_id)
            if f.id != folder_id and f.path.startswith(prefix)
        ]

    def breadcrumbs(self, workspace_id: uuid.UUID, folder_id: uuid.UUID) -> list[Breadcrumb]:
        crumbs: list[Breadcrumb] = []
        current: Folder | None = self.get(workspace_id, folder_id)
        while current is not None:
            crumbs.append(Breadcrumb(id=current.id, name=current.name))
            current = (
                self.folders.get_scoped(workspace_id, current.parent_id)
                if current.parent_id
                else None
            )
        return list(reversed(crumbs))

    def rename_or_move(
        self,
        workspace_id: uuid.UUID,
        folder: Folder,
        name: str | None,
        parent_id: uuid.UUID | None,
        move: bool,
    ) -> Folder:
        new_name = (name or folder.name).strip()
        new_parent_id = parent_id if move else folder.parent_id

        if new_parent_id == folder.id:
            raise ValidationError("A folder cannot be its own parent.")
        if move and new_parent_id in self.descendant_ids(workspace_id, folder.id):
            raise ValidationError("Cannot move a folder into its own descendant.")
        if self.folders.sibling_exists(workspace_id, new_parent_id, new_name) and (
            new_name != folder.name or new_parent_id != folder.parent_id
        ):
            raise ConflictError("A folder with this name already exists in the destination.")

        old_prefix = folder.path
        folder.name = new_name
        folder.parent_id = new_parent_id
        folder.path = self._resolve_path(workspace_id, new_parent_id, new_name)

        # Re-path descendants so breadcrumbs stay correct after a move/rename.
        for child in self.folders.list_for_workspace(workspace_id):
            if child.id != folder.id and child.path.startswith(old_prefix.rstrip("/") + "/"):
                child.path = folder.path.rstrip("/") + child.path[len(old_prefix.rstrip("/")):]
        self.db.flush()
        return folder

    def delete(self, folder: Folder) -> None:
        self.folders.delete(folder)
