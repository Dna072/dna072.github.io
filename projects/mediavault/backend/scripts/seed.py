"""Seed the database with a realistic demo workspace.

Idempotent: running it repeatedly will not duplicate the demo data. Creates
users, a workspace with mixed roles, a folder tree, tags and tagged assets
(with small generated placeholder files) so the UI has content on first run.

Usage:
    python -m scripts.seed
"""

from __future__ import annotations

import io
import sys

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.logging import configure_logging, get_logger
from app.models.enums import AssetKind, Role
from app.services.asset import AssetService
from app.services.auth import AuthService
from app.services.folder import FolderService
from app.services.tag import TagService
from app.services.workspace import WorkspaceService

logger = get_logger("mediavault.seed")

# Minimal valid 1x1 PNG used as a placeholder asset payload.
PNG_1x1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d4944415478da63f8cff0bf1f0005ff02fedca4b9740000000049454e44ae426082"
)

DEMO_USERS = [
    ("admin@mediavault.dev", "ChangeMe123!", "Ada Admin", Role.ADMIN),
    ("editor@mediavault.dev", "ChangeMe123!", "Ed Editor", Role.MEMBER),
    ("viewer@mediavault.dev", "ChangeMe123!", "Vi Viewer", Role.VIEWER),
]

FOLDERS = ["Brand Campaigns", "Product Launches", "Social Cuts", "Raw Footage"]
TAGS = [
    ("hero", "#0f766e"),
    ("approved", "#16a34a"),
    ("draft", "#f59e0b"),
    ("archive", "#64748b"),
]
ASSETS = [
    ("Spring Launch Teaser", "Hero teaser for the spring product launch.", "Brand Campaigns", ["hero", "approved"]),
    ("Product Reveal 30s", "30 second cutdown of the product reveal.", "Product Launches", ["approved"]),
    ("Behind The Scenes", "BTS footage from the studio shoot.", "Raw Footage", ["draft"]),
    ("Instagram Story 9x16", "Vertical social edit for stories.", "Social Cuts", ["draft"]),
    ("Founder Interview", "Long-form founder interview master.", "Brand Campaigns", ["archive"]),
    ("Holiday Promo", "Holiday season promotional spot.", "Product Launches", ["hero"]),
]


def seed() -> None:
    configure_logging(settings.LOG_LEVEL, json_output=False)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        auth = AuthService(db)
        # Users
        users = {}
        for email, password, name, _role in DEMO_USERS:
            existing = auth.users.get_by_email(email)
            if existing:
                users[email] = existing
                continue
            users[email] = auth.register(email, password, name)
        db.flush()

        admin = users["admin@mediavault.dev"]

        # Workspace (skip if already seeded)
        ws_service = WorkspaceService(db)
        workspace = ws_service.workspaces.get_by_slug("creative-studio")
        if workspace is None:
            workspace = ws_service.create(
                admin, "Creative Studio", "creative-studio", "Demo workspace for MediaVault."
            )
            db.flush()
            for email, _pw, _name, role in DEMO_USERS[1:]:
                ws_service.add_member(workspace, email, role)
            db.flush()
        else:
            logger.info("workspace already exists; ensuring content", fields={"slug": workspace.slug})

        # Folders
        folder_service = FolderService(db)
        folders = {}
        for name in FOLDERS:
            existing = next(
                (f for f in folder_service.folders.list_for_workspace(workspace.id) if f.name == name),
                None,
            )
            folders[name] = existing or folder_service.create(workspace.id, admin, name, None)
        db.flush()

        # Tags
        tag_service = TagService(db)
        tags = {name: tag_service.get_or_create(workspace.id, name, color) for name, color in TAGS}
        db.flush()

        # Assets
        from app.repositories.asset import AssetFilter

        asset_service = AssetService(db)
        for name, description, folder_name, tag_names in ASSETS:
            # Avoid duplicates on re-run.
            found, _ = asset_service.assets.search(
                AssetFilter(workspace_id=workspace.id, query=name), offset=0, limit=1
            )
            if any(a.name == name for a in found):
                continue
            asset = asset_service.upload(
                workspace.id,
                admin,
                fileobj=io.BytesIO(PNG_1x1),
                filename=f"{name.lower().replace(' ', '-')}.png",
                content_type="image/png",
                name=name,
                description=description,
                folder_id=folders[folder_name].id,
            )
            asset_service.set_tags(asset, [tags[t].id for t in tag_names])
        db.commit()

        logger.info(
            "seed complete",
            fields={
                "workspace": workspace.slug,
                "users": len(DEMO_USERS),
                "folders": len(FOLDERS),
                "tags": len(TAGS),
                "assets": len(ASSETS),
            },
        )
        print("\nSeed complete. Log in with:")
        for email, password, _name, role in DEMO_USERS:
            print(f"  {role.value:<7} {email} / {password}")
    except Exception:
        db.rollback()
        logger.exception("seed failed")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    sys.exit(0)
