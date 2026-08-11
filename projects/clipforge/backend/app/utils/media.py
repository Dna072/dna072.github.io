"""Thin wrappers around ffprobe/ffmpeg for media inspection and derivation.

Each function degrades gracefully: if the binary is missing or the input is not
decodable, it returns ``None`` / no output rather than raising, so a single bad
file never crashes the worker. All shell calls use argument lists (never
``shell=True``) to avoid injection.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class ProbeResult:
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    codec: str | None = None
    frame_rate: float | None = None
    bitrate: int | None = None


def ffprobe_available() -> bool:
    return shutil.which("ffprobe") is not None


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _parse_frame_rate(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    try:
        if "/" in value:
            num, den = value.split("/")
            den_f = float(den)
            return round(float(num) / den_f, 3) if den_f else None
        return float(value)
    except (ValueError, ZeroDivisionError):
        return None


def probe(path: str) -> ProbeResult:
    """Extract metadata from a media file using ffprobe."""
    if not ffprobe_available():
        logger.warning("ffprobe_missing", path=path)
        return ProbeResult()

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        path,
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)
        data = json.loads(out.stdout or "{}")
    except (subprocess.SubprocessError, json.JSONDecodeError) as exc:
        logger.warning("ffprobe_failed", path=path, error=str(exc))
        return ProbeResult()

    fmt: dict = data.get("format", {})
    video_stream: dict = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"), {}
    )

    def _to_float(v) -> float | None:
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _to_int(v) -> int | None:
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    return ProbeResult(
        duration_seconds=_to_float(fmt.get("duration")),
        width=_to_int(video_stream.get("width")),
        height=_to_int(video_stream.get("height")),
        codec=video_stream.get("codec_name"),
        frame_rate=_parse_frame_rate(video_stream.get("avg_frame_rate")),
        bitrate=_to_int(fmt.get("bit_rate")),
    )


def extract_thumbnail(path: str, output_path: str, *, at_seconds: float = 1.0) -> bool:
    """Grab a single frame as a JPEG thumbnail. Returns True on success."""
    if not ffmpeg_available():
        logger.warning("ffmpeg_missing", path=path)
        return False
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(max(0.0, at_seconds)),
        "-i",
        path,
        "-vframes",
        "1",
        "-vf",
        "scale=640:-2",
        output_path,
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=120, check=True)
        return True
    except subprocess.SubprocessError as exc:
        logger.warning("thumbnail_failed", path=path, error=str(exc))
        return False


def extract_audio(path: str, output_path: str) -> bool:
    """Extract a mono 16kHz WAV audio track (transcription-friendly)."""
    if not ffmpeg_available():
        logger.warning("ffmpeg_missing", path=path)
        return False
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        output_path,
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=300, check=True)
        return True
    except subprocess.SubprocessError as exc:
        logger.warning("audio_extract_failed", path=path, error=str(exc))
        return False
