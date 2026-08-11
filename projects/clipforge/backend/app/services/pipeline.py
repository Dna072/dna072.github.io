"""Video processing pipeline.

Executes the ordered stages for one job: metadata -> thumbnail -> audio ->
transcript -> AI insights. Each stage records its own status on the job so the UI
can show a live checklist, and a failure in a derived-asset stage (thumbnail /
audio) is non-fatal: the pipeline continues and still produces AI insights.

This module is deliberately framework-free (plain functions + a session) so it is
exercised directly in tests with the MockAIProvider, independent of Redis.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.job import JobStatus, ProcessingJob
from app.models.video import Video, VideoStatus
from app.services.ai.base import AIProvider
from app.services.ai.factory import get_ai_provider
from app.services.storage import LocalStorage, storage
from app.utils import media

logger = get_logger(__name__)


class PipelineError(Exception):
    pass


class ProcessingPipeline:
    def __init__(
        self,
        db: Session,
        *,
        ai: AIProvider | None = None,
        store: LocalStorage | None = None,
        worker_id: str = "worker",
    ) -> None:
        self.db = db
        self.ai = ai or get_ai_provider()
        self.storage = store or storage
        self.worker_id = worker_id

    # --- step bookkeeping ---------------------------------------------------
    def _set_step(self, job: ProcessingJob, name: str, status: str, detail: str | None = None):
        steps = list(job.steps or [])
        for step in steps:
            if step.get("name") == name:
                step["status"] = status
                if detail is not None:
                    step["detail"] = detail
                break
        else:
            steps.append({"name": name, "status": status, "detail": detail})
        job.steps = steps
        # JSON columns are not mutation-tracked by default; flag it explicitly so
        # the reassignment is always flushed.
        flag_modified(job, "steps")
        self.db.add(job)
        self.db.commit()

    # --- entrypoint ---------------------------------------------------------
    def run(self, job_id: str) -> ProcessingJob:
        job = self.db.get(ProcessingJob, job_id)
        if job is None:
            raise NotFoundError(f"Job {job_id} not found")
        video = self.db.get(Video, job.video_id)
        if video is None:
            raise NotFoundError(f"Video {job.video_id} not found")

        job.status = JobStatus.RUNNING
        job.attempts += 1
        job.worker_id = self.worker_id
        job.started_at = datetime.now(UTC)
        job.error_message = None
        video.status = VideoStatus.PROCESSING
        self.db.commit()

        log = logger.bind(job_id=job.id, video_id=video.id, provider=self.ai.name)
        log.info("pipeline_started")

        try:
            self._run_stages(job, video, log)
        except Exception as exc:  # pragma: no cover - defensive catch-all
            self._fail(job, video, str(exc))
            log.error("pipeline_failed", error=str(exc))
            if job.attempts < job.max_attempts:
                job.status = JobStatus.QUEUED
                video.status = VideoStatus.QUEUED
                self.db.commit()
            raise PipelineError(str(exc)) from exc

        job.status = JobStatus.SUCCEEDED
        job.finished_at = datetime.now(UTC)
        video.status = VideoStatus.COMPLETED
        self.db.commit()
        self.db.refresh(job)
        log.info("pipeline_succeeded")
        return job

    # --- stages -------------------------------------------------------------
    def _run_stages(self, job: ProcessingJob, video: Video, log) -> None:
        source_path = self.storage.path(video.storage_path)

        # 1. Metadata (ffprobe) -------------------------------------------------
        self._set_step(job, "metadata", "running")
        probe = media.probe(source_path)
        video.duration_seconds = probe.duration_seconds
        video.width = probe.width
        video.height = probe.height
        video.codec = probe.codec
        video.frame_rate = probe.frame_rate
        video.bitrate = probe.bitrate
        self.db.commit()
        self._set_step(job, "metadata", "succeeded")

        # 2. Thumbnail (ffmpeg) — non-fatal ------------------------------------
        self._set_step(job, "thumbnail", "running")
        thumb_key = f"videos/{video.id}/thumbnail.jpg"
        thumb_at = min(1.0, (video.duration_seconds or 2.0) / 2)
        if media.extract_thumbnail(source_path, self.storage.path(thumb_key), at_seconds=thumb_at):
            video.thumbnail_path = thumb_key
            self.db.commit()
            self._set_step(job, "thumbnail", "succeeded")
        else:
            self._set_step(job, "thumbnail", "skipped", "ffmpeg unavailable or frame error")

        # 3. Audio extraction (ffmpeg) — non-fatal -----------------------------
        self._set_step(job, "audio", "running")
        audio_key = f"videos/{video.id}/audio.wav"
        audio_ok = media.extract_audio(source_path, self.storage.path(audio_key))
        if audio_ok:
            video.audio_path = audio_key
            self.db.commit()
            self._set_step(job, "audio", "succeeded")
        else:
            self._set_step(job, "audio", "skipped", "ffmpeg unavailable or no audio track")

        # 4. Transcript (AI provider) ------------------------------------------
        self._set_step(job, "transcript", "running")
        audio_path = self.storage.path(audio_key) if audio_ok else source_path
        transcript = self.ai.transcribe(
            audio_path, duration_seconds=video.duration_seconds
        )
        video.transcript = transcript.text
        self.db.commit()
        self._set_step(job, "transcript", "succeeded", f"{len(transcript.segments)} segments")

        # 5. AI insights: summary + chapters + tags ----------------------------
        self._set_step(job, "ai_insights", "running")
        insights = self.ai.analyze(
            transcript.text,
            title=video.title,
            duration_seconds=video.duration_seconds,
        )
        video.summary = insights.summary
        video.chapters = [{"start": c.start, "title": c.title} for c in insights.chapters]
        video.tags = insights.tags
        self.db.commit()
        self._set_step(job, "ai_insights", "succeeded")

    def _fail(self, job: ProcessingJob, video: Video, message: str) -> None:
        job.status = JobStatus.FAILED
        job.error_message = message
        job.finished_at = datetime.now(UTC)
        video.status = VideoStatus.FAILED
        video.error_message = message
        # Mark the currently-running step as failed.
        for step in list(job.steps or []):
            if step.get("status") == "running":
                step["status"] = "failed"
                step["detail"] = message
        job.steps = list(job.steps or [])
        self.db.commit()
