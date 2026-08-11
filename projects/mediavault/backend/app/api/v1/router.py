from fastapi import APIRouter

from app.api.v1 import auth, folders, search, shares, tags, users, workspaces
from app.api.v1.assets import router as assets_router

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(workspaces.router)

# Folders/tags/assets/search are nested under a workspace_id path segment,
# so they are mounted with an explicit prefix rather than each declaring it.
api_router.include_router(
    folders.router, prefix="/workspaces/{workspace_id}"
)
api_router.include_router(tags.router, prefix="/workspaces/{workspace_id}")
api_router.include_router(assets_router, prefix="/workspaces/{workspace_id}")
api_router.include_router(search.router, prefix="/workspaces/{workspace_id}")

# Shares mixes workspace-scoped management routes with public token routes,
# so its own module owns the full paths.
api_router.include_router(shares.router)
