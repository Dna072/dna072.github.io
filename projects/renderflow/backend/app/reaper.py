"""Background reaper thread.

Periodically requeues jobs whose worker lease expired (the worker crashed or was
killed mid-job). Runs inside the API process so a lost worker never leaves a job
stuck in RUNNING forever.
"""

from __future__ import annotations

import logging
import threading

from .config import get_settings
from .service import reap_stuck_jobs

logger = logging.getLogger("renderflow.reaper")


class ReaperThread(threading.Thread):
    def __init__(self, session_factory, interval_seconds: float = 15.0) -> None:
        super().__init__(name="renderflow-reaper", daemon=True)
        self._session_factory = session_factory
        self._interval = interval_seconds
        self._stop = threading.Event()

    def run(self) -> None:
        settings = get_settings()
        logger.info("reaper started", extra={"interval_seconds": self._interval})
        while not self._stop.wait(self._interval):
            try:
                session = self._session_factory()
                try:
                    reap_stuck_jobs(session, settings=settings)
                finally:
                    session.close()
            except Exception:  # noqa: BLE001
                logger.exception("reaper iteration failed")

    def stop(self) -> None:
        self._stop.set()
