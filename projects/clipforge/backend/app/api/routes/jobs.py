"""Processing job endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.job import JobPublic
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobPublic)
def get_job(job_id: str, current_user: CurrentUser, db: DbSession) -> JobPublic:
    job = JobService(db).get(current_user, job_id)
    return JobPublic.model_validate(job)
