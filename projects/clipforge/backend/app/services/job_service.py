"""Processing job service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.job import ProcessingJob
from app.models.user import User
from app.repositories.job_repo import JobRepository


class JobService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.jobs = JobRepository(db)

    def get(self, user: User, job_id: str) -> ProcessingJob:
        job = self.jobs.get_for_owner(job_id, user.id)
        if not job:
            raise NotFoundError("Job not found.")
        return job

    def active_count(self, user: User) -> int:
        return self.jobs.count_active_for_owner(user.id)
