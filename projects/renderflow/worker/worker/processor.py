"""Dispatches a claimed `Job` to the right FFmpeg adapter function.

Output paths are derived deterministically from the job id
(`<job_id>.<ext>`), so re-running a job after a crash-before-commit simply
overwrites the same file rather than leaking a new one — this is what makes
the *side effect* idempotent even though delivery is only at-least-once.
"""

import logging
from pathlib import Path

from renderflow_common.enums import JobType
from renderflow_common.models import Job

from . import ffmpeg_adapter as ffmpeg
from .ffmpeg_adapter import ProcessingError, ProcessingResult

logger = logging.getLogger("renderflow.worker.processor")

_OUTPUT_EXTENSION = {
    JobType.TRANSCODE: "mp4",
    JobType.THUMBNAIL: "jpg",
    JobType.AUDIO_EXTRACT: "mp3",
}


def process_job(job: Job, storage_root: Path, force_mock: bool) -> ProcessingResult:
    input_path = ffmpeg.resolve_local_path(job.input_uri, storage_root)
    use_mock = ffmpeg.should_use_mock(force_mock, input_path)
    if use_mock:
        logger.info("job %s using mock ffmpeg adapter (job_type=%s)", job.id, job.job_type.value)

    if job.job_type == JobType.METADATA:
        return ffmpeg.process_metadata(input_path, job.params, use_mock)

    ext = _OUTPUT_EXTENSION[job.job_type]
    output_path = storage_root / "output" / f"{job.id}.{ext}"

    if job.job_type == JobType.TRANSCODE:
        return ffmpeg.process_transcode(input_path, output_path, job.params, use_mock)
    if job.job_type == JobType.THUMBNAIL:
        return ffmpeg.process_thumbnail(input_path, output_path, job.params, use_mock)
    if job.job_type == JobType.AUDIO_EXTRACT:
        return ffmpeg.process_audio_extract(input_path, output_path, job.params, use_mock)

    raise ProcessingError(f"unsupported job_type: {job.job_type}")
