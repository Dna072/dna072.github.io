from fastapi import APIRouter

from app.api.v1 import auth, dashboard, videos, workspaces

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(videos.router)
api_router.include_router(dashboard.router)

__all__ = ["api_router"]
