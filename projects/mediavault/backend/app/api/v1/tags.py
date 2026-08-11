import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import WorkspaceContext, require_member, require_viewer
from app.db.session import get_db
from app.models.tag import Tag, asset_tags
from app.schemas.common import Message
from app.schemas.tag import TagCreate, TagRead, TagUpdate

router = APIRouter(prefix="/tags", tags=["tags"])


def _to_read(db: Session, tag: Tag) -> TagRead:
    count = (
        db.query(func.count(asset_tags.c.asset_id)).filter(asset_tags.c.tag_id == tag.id).scalar()
        or 0
    )
    data = TagRead.model_validate(tag)
    data.asset_count = count
    return data


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(
    payload: TagCreate,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> TagRead:
    existing = (
        db.query(Tag)
        .filter(Tag.workspace_id == ctx.workspace_id, Tag.name == payload.name)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag already exists")
    tag = Tag(workspace_id=ctx.workspace_id, name=payload.name, color=payload.color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return _to_read(db, tag)


@router.get("", response_model=list[TagRead])
def list_tags(
    ctx: WorkspaceContext = Depends(require_viewer), db: Session = Depends(get_db)
) -> list[TagRead]:
    tags = (
        db.query(Tag).filter(Tag.workspace_id == ctx.workspace_id).order_by(Tag.name.asc()).all()
    )
    return [_to_read(db, t) for t in tags]


def _get_tag_or_404(db: Session, workspace_id: uuid.UUID, tag_id: uuid.UUID) -> Tag:
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.workspace_id == workspace_id).first()
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return tag


@router.patch("/{tag_id}", response_model=TagRead)
def update_tag(
    tag_id: uuid.UUID,
    payload: TagUpdate,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> TagRead:
    tag = _get_tag_or_404(db, ctx.workspace_id, tag_id)
    if payload.name is not None:
        tag.name = payload.name
    if payload.color is not None:
        tag.color = payload.color
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return _to_read(db, tag)


@router.delete("/{tag_id}", response_model=Message)
def delete_tag(
    tag_id: uuid.UUID,
    ctx: WorkspaceContext = Depends(require_member),
    db: Session = Depends(get_db),
) -> Message:
    tag = _get_tag_or_404(db, ctx.workspace_id, tag_id)
    db.delete(tag)
    db.commit()
    return Message(message="Tag deleted")
