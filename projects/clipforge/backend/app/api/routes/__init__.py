"""API route registration."""

from fastapi import APIRouter

from app.api.routes import (
    auth,
    dashboard,
    health,
    jobs,
    search,
    videos,
    workspaces,
)
from app.core.config import settings

# Health/readiness live at the root (no version prefix) for probes.
root_router = APIRouter()
root_router.include_router(health.router)

# Versioned API surface.
api_router = APIRouter(prefix=settings.api_v1_prefix)
api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(videos.router)
api_router.include_router(jobs.router)
api_router.include_router(search.router)
api_router.include_router(dashboard.router)

__all__ = ["root_router", "api_router"]
