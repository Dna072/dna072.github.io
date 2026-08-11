import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import WorkspaceContext, require_member, require_viewer
from app.db.session import get_db
from app.models.asset import Asset
from app.models.folder import Folder
from app.schemas.common import Message
from app.schemas.folder import FolderCreate, FolderRead, FolderUpdate

router = APIRouter(prefix="/folders", tags=["folders"])


def _to_read(db: Session, folder: Folder) -> FolderRead:
    asset_count = (
        db.query(func.count(Asset.id)).filter(Asset.folder_id == folder.id).scalar() or 0
    )
    subfolder_count = (
        db.query(func.count(Folder.id)).filter(Folder.parent_id == folder.id).scalar() or 0
    )
    data = FolderRead.model_validate(folder)
    data.asset_count = asset_count
    data.subfolder_count = subfolder_count
    return data


def _get_folder_or_404(db: Session, workspace_id: uuid.UUID, folder_id: uuid.UUID) -> Folder:
    folder = (
        db.query(Folder)
        .filter(Folder.id == folder_id, Folder.workspace_id == workspace_id)
        .first()
    )
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    return folder


def _recompute_descendant_paths(db: Session, folder: Folder) -> None:
    """After moving `folder`, cascade the new path prefix down to all descendants."""
    children = db.query(Folder).filter(Folder.parent_id == folder.id).all()
    for child in children:
        child.path = f"{folder.path}/{folder.id}" if folder.path else str(folder.id)
        db.add(child)
        _recompute_descendant_paths(db, child)


@router.post("", response_model=FolderRead, status_code=status.HTTP_201_CREATED)
def create_folder(
    payload: FolderCreate,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> FolderRead:
    parent_path = ""
    if payload.parent_id is not None:
        parent = _get_folder_or_404(db, ctx.workspace_id, payload.parent_id)
        parent_path = f"{parent.path}/{parent.id}" if parent.path else str(parent.id)
    folder = Folder(
        workspace_id=ctx.workspace_id,
        parent_id=payload.parent_id,
        name=payload.name,
        path=parent_path,
        created_by=ctx.user.id,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return _to_read(db, folder)


@router.get("", response_model=list[FolderRead])
def list_folders(
    parent_id: uuid.UUID | None = Query(default=None),
    ctx: WorkspaceContext = Depends(require_viewer),
    db: Session = Depends(get_db),
) -> list[FolderRead]:
    query = db.query(Folder).filter(Folder.workspace_id == ctx.workspace_id)
    query = query.filter(Folder.parent_id == parent_id) if parent_id else query.filter(
        Folder.parent_id.is_(None)
    )
    folders = query.order_by(Folder.name.asc()).all()
    return [_to_read(db, f) for f in folders]


@router.get("/{folder_id}", response_model=FolderRead)
def get_folder(
    folder_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(require_viewer),
    db: Session = Depends(get_db),
) -> FolderRead:
    folder = _get_folder_or_404(db, ctx.workspace_id, folder_id)
    return _to_read(db, folder)


@router.patch("/{folder_id}", response_model=FolderRead)
def update_folder(
    folder_id: uuid.UUID,
    payload: FolderUpdate,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> FolderRead:
    folder = _get_folder_or_404(db, ctx.workspace_id, folder_id)
    if payload.name is not None:
        folder.name = payload.name
    if "parent_id" in payload.model_fields_set:
        new_parent_id = payload.parent_id
        if new_parent_id == folder.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Folder cannot be its own parent"
            )
        new_path = ""
        if new_parent_id is not None:
            new_parent = _get_folder_or_404(db, ctx.workspace_id, new_parent_id)
            # A move is only a cycle if the destination is `folder` itself or
            # one of `folder`'s descendants — i.e. `folder.id` shows up in the
            # *new parent's* ancestor chain.
            new_parent_ancestor_ids = {
                uuid.UUID(p) for p in new_parent.path.split("/") if p
            }
            if folder.id in new_parent_ancestor_ids or new_parent.id == folder.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move a folder into its own descendant",
                )
            new_path = f"{new_parent.path}/{new_parent.id}" if new_parent.path else str(
                new_parent.id
            )
        folder.parent_id = new_parent_id
        folder.path = new_path
        db.add(folder)
        db.flush()
        _recompute_descendant_paths(db, folder)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return _to_read(db, folder)


@router.delete("/{folder_id}", response_model=Message)
def delete_folder(
    folder_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> Message:
    folder = _get_folder_or_404(db, ctx.workspace_id, folder_id)
    db.delete(folder)
    db.commit()
    return Message(message="Folder deleted")
