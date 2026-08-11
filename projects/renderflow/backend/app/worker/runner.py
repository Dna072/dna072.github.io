"""Worker runtime.

Responsibilities:
  * poll the shared queue for ready job ids,
  * atomically claim each job (RUNNING under a lease),
  * download the input, run the processor, store the output,
  * mark the job SUCCEEDED or FAILED (with retry/backoff handled by the service),
  * emit periodic heartbeats so the API/dashboard can show worker liveness,
  * shut down cleanly on SIGINT/SIGTERM (finish the in-flight job first).
"""

from __future__ import annotations

import logging
import os
import signal
import socket
import tempfile
import threading
import time
import uuid

from .. import service
from ..config import Settings, get_settings
from ..database import SessionLocal, init_db
from ..logging_config import configure_logging, job_id_ctx, worker_id_ctx
from ..queue import JobQueue, get_queue
from ..state_machine import JobType
from ..storage import ObjectStorage, get_storage
from .processors import ProcessingError, Processor

logger = logging.getLogger("renderflow.worker")


class Worker:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        queue: JobQueue | None = None,
        storage: ObjectStorage | None = None,
        worker_id: str | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.queue = queue or get_queue(self.settings)
        self.storage = storage or get_storage(self.settings)
        self.worker_id = worker_id or f"worker-{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:6]}"
        self.hostname = socket.gethostname()
        self._stop = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None
        self._current_job_id: str | None = None
        self._status = "idle"
        self.jobs_processed = 0
        self.jobs_failed = 0
        worker_id_ctx.set(self.worker_id)

    # --- lifecycle ------------------------------------------------------- #
    def start(self) -> None:
        logger.info("worker starting", extra={"worker_id": self.worker_id})
        self._install_signal_handlers()
        self._start_heartbeat()
        try:
            self._loop()
        finally:
            self._emit_heartbeat(status="stopped")
            logger.info(
                "worker stopped",
                extra={
                    "worker_id": self.worker_id,
                    "jobs_processed": self.jobs_processed,
                    "jobs_failed": self.jobs_failed,
                },
            )

    def stop(self) -> None:
        self._stop.set()

    def _install_signal_handlers(self) -> None:
        def handler(signum, _frame):
            logger.info("received signal; draining", extra={"signal": signum})
            self.stop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, handler)
            except ValueError:
                # Not on the main thread (e.g. under tests) — skip.
                pass

    # --- heartbeat ------------------------------------------------------- #
    def _start_heartbeat(self) -> None:
        def beat() -> None:
            while not self._stop.wait(self.settings.worker_heartbeat_interval_seconds):
                self._emit_heartbeat(status=self._status)

        self._emit_heartbeat(status="idle")
        self._heartbeat_thread = threading.Thread(
            target=beat, name=f"heartbeat-{self.worker_id}", daemon=True
        )
        self._heartbeat_thread.start()

    def _emit_heartbeat(self, *, status: str) -> None:
        self._touch_liveness_file()
        try:
            session = SessionLocal()
            try:
                service.record_heartbeat(
                    session,
                    self.worker_id,
                    hostname=self.hostname,
                    status=status,
                    current_job_id=self._current_job_id,
                    jobs_processed=self.jobs_processed,
                    jobs_failed=self.jobs_failed,
                )
            finally:
                session.close()
        except Exception:  # noqa: BLE001
            logger.exception("failed to emit heartbeat")

    def _touch_liveness_file(self) -> None:
        """Touch a file so a K8s exec probe can verify the loop is alive."""
        try:
            path = self.settings.worker_liveness_file
            with open(path, "w") as fh:
                fh.write(str(time.time()))
        except OSError:
            pass

    # --- main loop ------------------------------------------------------- #
    def _loop(self) -> None:
        while not self._stop.is_set():
            job_id = self.queue.dequeue()
            if job_id is None:
                time.sleep(self.settings.worker_poll_interval_seconds)
                continue
            self.run_once(job_id)

    def run_once(self, job_id: str) -> None:
        """Claim and process a single job id. Public for testing."""
        token = job_id_ctx.set(job_id)
        session = SessionLocal()
        try:
            job = service.claim_job(session, job_id, self.worker_id, settings=self.settings)
            if job is None:
                logger.info("job no longer claimable; skipping", extra={"job_id": job_id})
                return
            self._current_job_id = job_id
            self._status = "busy"
            self._emit_heartbeat(status="busy")
            self._process(session, job)
        except Exception as exc:  # noqa: BLE001
            logger.exception("unexpected worker error", extra={"job_id": job_id})
            self.jobs_failed += 1
            try:
                service.fail_job(session, job_id, error_message=str(exc), settings=self.settings)
            except Exception:  # noqa: BLE001
                logger.exception("failed to record job failure", extra={"job_id": job_id})
        finally:
            self._current_job_id = None
            self._status = "idle"
            self._emit_heartbeat(status="idle")
            session.close()
            job_id_ctx.reset(token)

    def _process(self, session, job) -> None:
        params = job.params or {}
        # Deterministic failure hook for demos/tests of the retry path.
        if params.get("force_fail"):
            self.jobs_failed += 1
            service.fail_job(
                session, job.id,
                error_message="forced failure (force_fail param)",
                settings=self.settings,
            )
            return

        with tempfile.TemporaryDirectory(prefix="renderflow-") as tmp:
            input_local = self._fetch_input(job.input_uri, tmp)
            processor = Processor(self.settings, work_dir=tmp)
            result = processor.process(JobType(job.job_type), input_local, params)

            output_uri = None
            if result.output_path:
                key = f"{job.id}/{os.path.basename(result.output_path)}"
                output_uri = self.storage.save(result.output_path, key)

            service.complete_job(
                session, job.id, output_uri=output_uri, result=result.result
            )
            self.jobs_processed += 1

    def _fetch_input(self, input_uri: str, tmp: str) -> str:
        """Return a local path for the input, downloading http(s) if needed."""
        if input_uri.startswith(("http://", "https://")):
            return self._download_http(input_uri, tmp)
        try:
            return self.storage.open_local(input_uri)
        except Exception as exc:  # noqa: BLE001
            raise ProcessingError(f"could not open input {input_uri}: {exc}") from exc

    @staticmethod
    def _download_http(url: str, tmp: str) -> str:
        import urllib.request

        dest = os.path.join(tmp, "input_" + os.path.basename(url.split("?")[0] or "media"))
        try:
            urllib.request.urlretrieve(url, dest)  # noqa: S310 - trusted internal use
        except Exception as exc:  # noqa: BLE001
            raise ProcessingError(f"failed to download {url}: {exc}") from exc
        return dest


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, "renderflow-worker")
    init_db()
    Worker(settings=settings).start()


if __name__ == "__main__":
    main()
