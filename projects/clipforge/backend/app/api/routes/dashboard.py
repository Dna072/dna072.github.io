"""Dashboard / stats endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.dashboard import DashboardStats
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(current_user: CurrentUser, db: DbSession) -> DashboardStats:
    return DashboardService(db).stats(current_user)
