"""Media processors.

Each processor takes an input file and job params and produces an output plus a
result dict. Real work is done with ffmpeg/ffprobe; when those binaries are
missing (e.g. minimal CI images) or ``force_mock_processing`` is set, a
deterministic mock output is produced instead so the full pipeline — dequeue,
process, store, complete — still exercises end to end.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..config import Settings
from ..state_machine import JobType

logger = logging.getLogger("renderflow.processor")


class ProcessingError(Exception):
    """Raised when a processor cannot complete the job."""


@dataclass
class ProcessResult:
    output_path: str | None
    result: dict


def ffmpeg_available(settings: Settings) -> bool:
    if settings.force_mock_processing:
        return False
    return shutil.which(settings.ffmpeg_binary) is not None


def _run(cmd: list[str], timeout: float = 3600.0) -> str:
    logger.info("running command", extra={"command": " ".join(cmd)})
    try:
        proc = subprocess.run(  # noqa: S603 - cmd is built from a fixed binary + validated params
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise ProcessingError(f"binary not found: {cmd[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise ProcessingError(
            f"command failed ({exc.returncode}): {exc.stderr[-2000:]}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ProcessingError("command timed out") from exc
    return proc.stdout


class Processor:
    """Base class dispatching to per-job-type logic."""

    def __init__(self, settings: Settings, work_dir: str) -> None:
        self.settings = settings
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.mock = not ffmpeg_available(settings)

    def process(self, job_type: JobType, input_path: str, params: dict) -> ProcessResult:
        handler = {
            JobType.TRANSCODE: self._transcode,
            JobType.THUMBNAIL: self._thumbnail,
            JobType.AUDIO_EXTRACT: self._audio_extract,
            JobType.METADATA: self._metadata,
        }.get(job_type)
        if handler is None:
            raise ProcessingError(f"unsupported job type: {job_type}")
        return handler(input_path, params)

    # --- transcode ------------------------------------------------------- #
    def _transcode(self, input_path: str, params: dict) -> ProcessResult:
        height = int(params.get("height", 720))
        codec = params.get("video_codec", "libx264")
        container = params.get("container", "mp4")
        out = self.work_dir / f"transcoded_{height}p.{container}"
        if self.mock:
            _write_mock(out, f"transcoded to {height}p ({codec})")
        else:
            _run(
                [
                    self.settings.ffmpeg_binary, "-y", "-i", input_path,
                    "-vf", f"scale=-2:{height}", "-c:v", codec,
                    "-c:a", "aac", str(out),
                ]
            )
        return ProcessResult(
            output_path=str(out),
            result={"height": height, "codec": codec, "container": container, "mock": self.mock},
        )

    # --- thumbnail ------------------------------------------------------- #
    def _thumbnail(self, input_path: str, params: dict) -> ProcessResult:
        timestamp = params.get("timestamp", "00:00:01")
        width = int(params.get("width", 320))
        out = self.work_dir / "thumbnail.jpg"
        if self.mock:
            _write_mock(out, f"thumbnail @ {timestamp} w={width}")
        else:
            _run(
                [
                    self.settings.ffmpeg_binary, "-y", "-ss", str(timestamp),
                    "-i", input_path, "-vframes", "1",
                    "-vf", f"scale={width}:-1", str(out),
                ]
            )
        return ProcessResult(
            output_path=str(out),
            result={"timestamp": timestamp, "width": width, "mock": self.mock},
        )

    # --- audio extract --------------------------------------------------- #
    def _audio_extract(self, input_path: str, params: dict) -> ProcessResult:
        fmt = params.get("format", "mp3")
        bitrate = params.get("bitrate", "192k")
        out = self.work_dir / f"audio.{fmt}"
        if self.mock:
            _write_mock(out, f"audio {fmt} @ {bitrate}")
        else:
            _run(
                [
                    self.settings.ffmpeg_binary, "-y", "-i", input_path,
                    "-vn", "-b:a", bitrate, str(out),
                ]
            )
        return ProcessResult(
            output_path=str(out),
            result={"format": fmt, "bitrate": bitrate, "mock": self.mock},
        )

    # --- metadata -------------------------------------------------------- #
    def _metadata(self, input_path: str, params: dict) -> ProcessResult:
        if self.mock:
            metadata = {
                "format": {"duration": "0", "size": str(_safe_size(input_path))},
                "streams": [],
                "mock": True,
            }
        else:
            stdout = _run(
                [
                    self.settings.ffprobe_binary, "-v", "quiet",
                    "-print_format", "json", "-show_format", "-show_streams",
                    input_path,
                ]
            )
            metadata = json.loads(stdout)
            metadata["mock"] = False
        return ProcessResult(output_path=None, result=metadata)


def _write_mock(path: Path, note: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"RENDERFLOW-MOCK-OUTPUT\n{note}\n")


def _safe_size(path: str) -> int:
    try:
        return Path(path).stat().st_size
    except OSError:
        return 0
