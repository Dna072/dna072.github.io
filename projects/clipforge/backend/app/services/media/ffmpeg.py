"""Media processing helpers wrapping ffmpeg/ffprobe.

Every function degrades gracefully when ffmpeg is not installed or the input is
not a real media file (as in demo mode). In that case deterministic mock values
are returned so the pipeline still advances through every stage.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger("clipforge.media")


@dataclass
class ProbeResult:
    duration: float
    width: int | None
    height: int | None
    has_audio: bool
    is_mock: bool = False


def ffmpeg_available() -> bool:
    """Return True when both ffmpeg and ffprobe are on PATH."""
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def _mock_probe(source: Path) -> ProbeResult:
    # Derive stable pseudo-metadata from the file size so demos look realistic.
    size = source.stat().st_size if source.exists() else 1024
    duration = round(60 + (size % 240), 2)
    return ProbeResult(
        duration=duration, width=1920, height=1080, has_audio=True, is_mock=True
    )


def probe(source: str) -> ProbeResult:
    """Return media metadata using ffprobe, or mock values if unavailable."""
    path = Path(source)
    if not ffmpeg_available():
        logger.info("ffprobe_unavailable_using_mock")
        return _mock_probe(path)
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        data = json.loads(proc.stdout or "{}")
        fmt = data.get("format", {})
        streams = data.get("streams", [])
        video_stream = next(
            (s for s in streams if s.get("codec_type") == "video"), None
        )
        has_audio = any(s.get("codec_type") == "audio" for s in streams)
        duration = float(fmt.get("duration", 0.0) or 0.0)
        if duration <= 0 or video_stream is None:
            # Input isn't decodable (e.g. a placeholder file) -> mock.
            return _mock_probe(path)
        return ProbeResult(
            duration=round(duration, 2),
            width=video_stream.get("width"),
            height=video_stream.get("height"),
            has_audio=has_audio,
        )
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.warning("ffprobe_failed", extra={"error": str(exc)})
        return _mock_probe(path)


def extract_thumbnail(source: str, dest: str, *, at_seconds: float = 1.0) -> bool:
    """Extract a single thumbnail frame. Returns True on real extraction."""
    path = Path(source)
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if not ffmpeg_available():
        _write_placeholder(dest_path, b"THUMBNAIL")
        return False
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(at_seconds),
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-q:v",
                "3",
                str(dest_path),
            ],
            capture_output=True,
            timeout=120,
            check=True,
        )
        if dest_path.exists() and dest_path.stat().st_size > 0:
            return True
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.warning("thumbnail_failed", extra={"error": str(exc)})
    _write_placeholder(dest_path, b"THUMBNAIL")
    return False


def extract_audio(source: str, dest: str) -> bool:
    """Extract mono 16kHz WAV audio. Returns True on real extraction."""
    path = Path(source)
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if not ffmpeg_available():
        _write_placeholder(dest_path, b"AUDIO")
        return False
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                str(dest_path),
            ],
            capture_output=True,
            timeout=300,
            check=True,
        )
        if dest_path.exists() and dest_path.stat().st_size > 0:
            return True
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.warning("audio_extract_failed", extra={"error": str(exc)})
    _write_placeholder(dest_path, b"AUDIO")
    return False


def _write_placeholder(dest: Path, marker: bytes) -> None:
    """Write a tiny placeholder artifact so downstream paths exist."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(marker)
