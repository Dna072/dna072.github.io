"""Aggregate all v1 routers under a single APIRouter."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routers import (
    assets,
    auth,
    folders,
    health,
    public,
    search,
    shares,
    tags,
    users,
    workspaces,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(workspaces.router)
api_router.include_router(folders.router)
api_router.include_router(tags.router)
api_router.include_router(assets.router)
api_router.include_router(shares.router)
api_router.include_router(search.router)
api_router.include_router(public.router)
