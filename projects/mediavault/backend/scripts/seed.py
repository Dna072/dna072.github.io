#!/usr/bin/env python
"""Seed the database with a realistic demo dataset.

Creates two workspaces, three users (admin/member/viewer), a small folder
tree, a tag palette, and a batch of placeholder "video" assets tagged and
distributed across folders — enough to exercise the grid/table UI, search,
filters, and RBAC without needing real video files.

Usage (from backend/):
    python -m scripts.seed
    # or, inside the API container:
    python scripts/seed.py

Idempotent: running it twice will not create duplicate users/workspaces
(matched by email/slug), but will add fresh demo assets each run.
"""

import io
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.models.asset import Asset, AssetStatus  # noqa: E402
from app.models.folder import Folder  # noqa: E402
from app.models.membership import WorkspaceMembership, WorkspaceRole  # noqa: E402
from app.models.tag import Tag  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.workspace import Workspace  # noqa: E402
from app.services.storage import LocalStorage  # noqa: E402

# A minimal-but-valid 1x1 transparent PNG, used as placeholder "poster" bytes
# for image assets so downloads/streaming actually work end-to-end.
_TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d494844520000000100000001080600000"
    "01f15c4890000000a49444154789c6360000002000155e2802d0000000049454e44ae426082"
)

DEMO_USERS = [
    ("admin@mediavault.dev", "Ava Martinez", WorkspaceRole.ADMIN),
    ("editor@mediavault.dev", "Jordan Lee", WorkspaceRole.MEMBER),
    ("client@mediavault.dev", "Priya Shah", WorkspaceRole.VIEWER),
]
DEMO_PASSWORD = "demopass123"

FOLDER_TREE = {
    "Brand Campaigns": ["Q1 Launch", "Q2 Refresh"],
    "Social Cuts": ["Reels", "Stories"],
    "Raw Footage": [],
}

TAGS = [
    ("hero", "#2f6f5e"),
    ("final-cut", "#1f4f46"),
    ("raw", "#7a8c86"),
    ("approved", "#3f8f6f"),
    ("needs-review", "#c17a3f"),
    ("thumbnail", "#4a6f8f"),
]

ASSET_TITLES = [
    "product_launch_teaser",
    "founder_interview_bts",
    "spring_campaign_hero",
    "social_reel_v1",
    "social_reel_v2",
    "client_testimonial_priya",
    "explainer_animation_final",
    "office_culture_reel",
    "conference_keynote_highlight",
    "brand_anthem_60s",
    "unboxing_video_draft",
    "press_kit_montage",
]

CONTENT_TYPES = ["video/mp4", "video/quicktime", "image/png"]


def _placeholder_bytes(content_type: str, title: str) -> bytes:
    if content_type == "image/png":
        return _TINY_PNG
    text = (
        f"MediaVault demo placeholder for '{title}'.\n"
        "This is not a real video file — seed data ships without binary "
        "video payloads to keep the repository small. Replace by uploading "
        "real media through the UI or API.\n"
    )
    return text.encode("utf-8") * 20


def get_or_create_user(db, email: str, full_name: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(email=email, full_name=full_name, hashed_password=hash_password(DEMO_PASSWORD))
    db.add(user)
    db.flush()
    return user


def get_or_create_workspace(db, name: str, slug: str, owner: User) -> Workspace:
    workspace = db.query(Workspace).filter(Workspace.slug == slug).first()
    if workspace:
        return workspace
    workspace = Workspace(name=name, slug=slug, owner_id=owner.id)
    db.add(workspace)
    db.flush()
    return workspace


def ensure_membership(db, workspace: Workspace, user: User, role: WorkspaceRole) -> None:
    existing = (
        db.query(WorkspaceMembership)
        .filter(
            WorkspaceMembership.workspace_id == workspace.id,
            WorkspaceMembership.user_id == user.id,
        )
        .first()
    )
    if existing:
        existing.role = role
        db.add(existing)
        return
    db.add(WorkspaceMembership(workspace_id=workspace.id, user_id=user.id, role=role))


def build_folders(db, workspace: Workspace, creator: User) -> list[Folder]:
    all_folders: list[Folder] = []
    for parent_name, children in FOLDER_TREE.items():
        parent = (
            db.query(Folder)
            .filter(Folder.workspace_id == workspace.id, Folder.name == parent_name)
            .first()
        )
        if not parent:
            parent = Folder(
                workspace_id=workspace.id, name=parent_name, path="", created_by=creator.id
            )
            db.add(parent)
            db.flush()
        all_folders.append(parent)
        for child_name in children:
            child = (
                db.query(Folder)
                .filter(Folder.workspace_id == workspace.id, Folder.name == child_name)
                .first()
            )
            if not child:
                child = Folder(
                    workspace_id=workspace.id,
                    name=child_name,
                    parent_id=parent.id,
                    path=str(parent.id),
                    created_by=creator.id,
                )
                db.add(child)
                db.flush()
            all_folders.append(child)
    return all_folders


def build_tags(db, workspace: Workspace) -> list[Tag]:
    tags = []
    for name, color in TAGS:
        tag = (
            db.query(Tag)
            .filter(Tag.workspace_id == workspace.id, Tag.name == name)
            .first()
        )
        if not tag:
            tag = Tag(workspace_id=workspace.id, name=name, color=color)
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


def build_assets(
    db, workspace: Workspace, owner: User, folders: list[Folder], tags: list[Tag]
) -> None:
    storage = LocalStorage()
    rng = random.Random(42)
    for title in ASSET_TITLES:
        content_type = rng.choice(CONTENT_TYPES)
        extension = {"video/mp4": "mp4", "video/quicktime": "mov", "image/png": "png"}[
            content_type
        ]
        filename = f"{title}.{extension}"
        payload = _placeholder_bytes(content_type, title)
        key = storage.build_key(workspace.id, filename)
        size, checksum = storage.save(key, io.BytesIO(payload))
        folder = rng.choice([*folders, None])
        asset = Asset(
            workspace_id=workspace.id,
            folder_id=folder.id if folder else None,
            owner_id=owner.id,
            filename=filename,
            original_filename=filename,
            description=f"Demo asset: {title.replace('_', ' ')}",
            content_type=content_type,
            size_bytes=size,
            storage_key=key,
            checksum_sha256=checksum,
            status=AssetStatus.READY,
        )
        asset.tags = rng.sample(tags, k=rng.randint(0, 3))
        db.add(asset)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        users = {
            email: get_or_create_user(db, email, name) for email, name, _ in DEMO_USERS
        }
        db.flush()

        admin_email = DEMO_USERS[0][0]
        workspace = get_or_create_workspace(
            db, "Acme Creative Studio", "acme-creative", users[admin_email]
        )
        for email, _, role in DEMO_USERS:
            ensure_membership(db, workspace, users[email], role)

        second_workspace = get_or_create_workspace(
            db, "Nimbus Films", "nimbus-films", users[admin_email]
        )
        ensure_membership(db, second_workspace, users[admin_email], WorkspaceRole.ADMIN)

        folders = build_folders(db, workspace, users[admin_email])
        tags = build_tags(db, workspace)
        build_assets(db, workspace, users[admin_email], folders, tags)

        db.commit()
        print("Seed complete.")
        print("Workspaces: acme-creative, nimbus-films")
        print("Demo accounts (password for all: %s):" % DEMO_PASSWORD)
        for email, name, role in DEMO_USERS:
            print(f"  - {email} ({name}) -> {role.value} on acme-creative")
    finally:
        db.close()


if __name__ == "__main__":
    main()
