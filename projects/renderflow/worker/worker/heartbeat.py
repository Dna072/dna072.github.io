"""Background heartbeat thread.

Runs independently of the main claim/process loop so it keeps ticking even
while the main thread is blocked inside a (potentially slow) FFmpeg
subprocess call. It does two things on every tick:

1. Upserts this worker's row in `workers` (status, current job, timestamps)
   so the ops UI's worker list is always close to real-time.
2. Touches `heartbeat_at` on the job currently being processed (if any) so
   the API's reaper (`app/scheduler.py`) knows this worker is still alive.

If a worker crashes, both of these simply stop updating and the reaper
notices the stale `heartbeat_at` after `HEARTBEAT_TIMEOUT_SECONDS`.
"""

import logging
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from renderflow_common.enums import WorkerStatus
from renderflow_common.models import Job, Worker
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger("renderflow.worker.heartbeat")


@dataclass
class WorkerState:
    worker_id: str
    hostname: str
    pid: int
    status: WorkerStatus = WorkerStatus.IDLE
    current_job_id: uuid.UUID | None = None
    jobs_processed: int = 0
    jobs_failed: int = 0


class HeartbeatReporter:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        state: WorkerState,
        interval_seconds: float,
    ):
        self._session_factory = session_factory
        self.state = state
        self._interval = interval_seconds
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, daemon=True, name="heartbeat")

    def start(self) -> None:
        self._register()
        self._thread.start()

    def stop(self, mark_offline: bool = True) -> None:
        self._stop_event.set()
        self._thread.join(timeout=self._interval + 5)
        if mark_offline:
            self._set_status(WorkerStatus.OFFLINE, current_job_id=None)

    def set_busy(self, job_id: uuid.UUID) -> None:
        with self._lock:
            self.state.status = WorkerStatus.BUSY
            self.state.current_job_id = job_id
        self._tick()

    def set_idle(self, *, success: bool | None = None) -> None:
        with self._lock:
            if success is True:
                self.state.jobs_processed += 1
            elif success is False:
                self.state.jobs_failed += 1
            self.state.status = WorkerStatus.IDLE
            self.state.current_job_id = None
        self._tick()

    def _run(self) -> None:
        while not self._stop_event.wait(self._interval):
            try:
                self._tick()
            except Exception:  # pragma: no cover - defensive
                logger.exception("heartbeat tick failed")

    def _register(self) -> None:
        db = self._session_factory()
        try:
            now = datetime.now(UTC)
            db.merge(
                Worker(
                    id=self.state.worker_id,
                    hostname=self.state.hostname,
                    pid=self.state.pid,
                    status=self.state.status,
                    current_job_id=self.state.current_job_id,
                    jobs_processed=self.state.jobs_processed,
                    jobs_failed=self.state.jobs_failed,
                    started_at=now,
                    last_heartbeat=now,
                )
            )
            db.commit()
        finally:
            db.close()

    def _tick(self) -> None:
        db = self._session_factory()
        try:
            with self._lock:
                status = self.state.status
                current_job_id = self.state.current_job_id
                jobs_processed = self.state.jobs_processed
                jobs_failed = self.state.jobs_failed

            now = datetime.now(UTC)
            worker = db.get(Worker, self.state.worker_id)
            if worker is None:
                worker = Worker(id=self.state.worker_id, hostname=self.state.hostname, pid=self.state.pid)
                db.add(worker)
            worker.status = status
            worker.current_job_id = current_job_id
            worker.jobs_processed = jobs_processed
            worker.jobs_failed = jobs_failed
            worker.last_heartbeat = now

            if current_job_id is not None:
                job = db.get(Job, current_job_id)
                if job is not None:
                    job.heartbeat_at = now

            db.commit()
        finally:
            db.close()

    def _set_status(self, status: WorkerStatus, current_job_id: uuid.UUID | None) -> None:
        with self._lock:
            self.state.status = status
            self.state.current_job_id = current_job_id
        try:
            self._tick()
        except Exception:  # pragma: no cover - best effort on shutdown
            logger.exception("failed to report final worker status")
