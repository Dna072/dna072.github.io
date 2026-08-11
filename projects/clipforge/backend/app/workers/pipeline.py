"""The core video processing pipeline.

Runs a job through discrete, observable stages. Each stage updates the job's
status/progress/stage_history so the UI can render a live timeline. The
pipeline is deliberately resilient: media steps fall back to mock artifacts
when ffmpeg is unavailable, and AI steps use whichever provider is configured.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.enums import JobStage, JobStatus, VideoStatus
from app.models.job import ProcessingJob
from app.models.video import Video
from app.services.ai.base import AIProvider
from app.services.ai.factory import get_ai_provider
from app.services.media import ffmpeg
from app.utils.files import video_dir

logger = get_logger("clipforge.pipeline")


class PipelineError(Exception):
    """Raised when a pipeline stage fails irrecoverably."""


def _record_stage(job: ProcessingJob, stage: JobStage, progress: int, note: str) -> None:
    job.stage = stage
    job.progress = progress
    history = list(job.stage_history or [])
    history.append(
        {
            "stage": stage.value,
            "progress": progress,
            "note": note,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    job.stage_history = history


def run_pipeline(db: Session, job_id: str, ai: AIProvider | None = None) -> ProcessingJob:
    """Execute the full processing pipeline for a job (synchronous)."""
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise PipelineError(f"Job {job_id} not found")
    video = db.get(Video, job.video_id)
    if video is None:
        raise PipelineError(f"Video for job {job_id} not found")

    ai = ai or get_ai_provider()
    job.status = JobStatus.RUNNING
    job.attempts += 1
    job.started_at = datetime.now(timezone.utc)
    job.error_message = None
    video.status = VideoStatus.PROCESSING
    _record_stage(job, JobStage.QUEUED, 5, "Job picked up by worker")
    db.commit()

    logger.info(
        "pipeline_started",
        extra={"job_id": job.id, "video_id": video.id, "ai_provider": ai.name},
    )

    try:
        workdir = video_dir(video.id)

        # --- Probe -------------------------------------------------------
        probe = ffmpeg.probe(video.storage_path)
        video.duration_seconds = probe.duration
        video.width = probe.width
        video.height = probe.height
        _record_stage(
            job,
            JobStage.PROBE,
            20,
            f"Probed media ({'mock' if probe.is_mock else 'ffprobe'})",
        )
        db.commit()

        # --- Thumbnail ---------------------------------------------------
        thumb_path = str(workdir / "thumbnail.jpg")
        ffmpeg.extract_thumbnail(
            video.storage_path, thumb_path, at_seconds=min(1.0, probe.duration / 2)
        )
        video.thumbnail_path = thumb_path
        _record_stage(job, JobStage.THUMBNAIL, 40, "Generated thumbnail")
        db.commit()

        # --- Audio -------------------------------------------------------
        audio_path = str(workdir / "audio.wav")
        ffmpeg.extract_audio(video.storage_path, audio_path)
        _record_stage(job, JobStage.AUDIO, 55, "Extracted audio track")
        db.commit()

        # --- Transcript --------------------------------------------------
        transcript = ai.transcribe(audio_path, duration=probe.duration)
        video.transcript = transcript.text
        _record_stage(job, JobStage.TRANSCRIPT, 70, "Transcribed audio")
        db.commit()

        # --- AI analysis -------------------------------------------------
        analysis = ai.analyze(transcript.text, duration=probe.duration)
        video.summary = analysis.summary
        video.chapters = [
            {"title": c.title, "start": c.start, "end": c.end}
            for c in analysis.chapters
        ]
        video.tags = analysis.tags
        _record_stage(job, JobStage.AI_ANALYSIS, 90, "Generated summary, chapters, tags")
        db.commit()

        # --- Persist / finish -------------------------------------------
        _record_stage(job, JobStage.PERSIST, 95, "Persisted results")
        video.status = VideoStatus.READY
        job.status = JobStatus.COMPLETED
        job.finished_at = datetime.now(timezone.utc)
        _record_stage(job, JobStage.DONE, 100, "Processing complete")
        db.commit()

        logger.info(
            "pipeline_completed", extra={"job_id": job.id, "video_id": video.id}
        )
        return job

    except Exception as exc:  # noqa: BLE001 - convert to job failure state
        db.rollback()
        job = db.get(ProcessingJob, job_id)
        video = db.get(Video, job.video_id) if job else None
        if job is not None:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            job.finished_at = datetime.now(timezone.utc)
        if video is not None:
            video.status = VideoStatus.FAILED
            video.error_message = str(exc)
        db.commit()
        logger.exception("pipeline_failed", extra={"job_id": job_id})
        raise PipelineError(str(exc)) from exc
