"""FFmpeg integration with an automatic mock fallback.

The mock path exists so CI, portfolio demos and any environment without a
real `ffmpeg`/`ffprobe` binary (or without real source media) can still run
the full job lifecycle end-to-end. It's selected automatically — no flags
needed — whenever a real run isn't possible; `FORCE_MOCK_FFMPEG=true` forces
it unconditionally (useful for fast, deterministic tests).
"""

import json
import logging
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("renderflow.worker.ffmpeg")


class ProcessingError(Exception):
    """Raised when media processing fails; the worker records `str(exc)`
    on the job and decides retry vs. dead-letter based on retry count."""


@dataclass
class ProcessingResult:
    output_uri: str | None
    result: dict[str, Any]


def resolve_local_path(uri: str, storage_root: Path) -> Path:
    """Map a job's `input_uri`/`output_uri` onto a local filesystem path.

    Supports plain paths, `file://` URIs, and relative paths (resolved under
    `storage_root`, the shared media volume in Compose/K8s). Object-store
    URIs (`s3://...`) are accepted as opaque identifiers: in the AWS
    deployment sketch (see README) they'd be downloaded/uploaded via boto3
    here instead of touched on the local filesystem.
    """
    if uri.startswith("file://"):
        return Path(uri[len("file://") :])
    p = Path(uri)
    if p.is_absolute():
        return p
    return storage_root / p


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def should_use_mock(force_mock: bool, input_path: Path) -> bool:
    if force_mock:
        return True
    if not ffmpeg_available():
        return True
    if not input_path.exists():
        # No real source media to operate on (typical for portfolio/demo
        # job submissions) - fabricate a plausible result instead of
        # failing every job with "file not found".
        return True
    return False


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise ProcessingError(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr[-2000:]}")
    return proc.stdout


def _mock_delay() -> None:
    # Small, deliberate delay so heartbeats/queue-depth are visible in the
    # ops UI even for mock jobs, without slowing tests down meaningfully.
    time.sleep(0.2)


def process_transcode(
    input_path: Path, output_path: Path, params: dict[str, Any], use_mock: bool
) -> ProcessingResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    codec = params.get("codec", "libx264")
    resolution = params.get("resolution")

    if use_mock:
        _mock_delay()
        output_path.write_text(
            json.dumps({"mock": True, "source": str(input_path), "codec": codec}, indent=2)
        )
        return ProcessingResult(
            output_uri=str(output_path),
            result={"mock": True, "codec": codec, "resolution": resolution},
        )

    cmd = ["ffmpeg", "-y", "-i", str(input_path), "-c:v", codec]
    if resolution:
        cmd += ["-vf", f"scale={resolution}"]
    cmd.append(str(output_path))
    _run(cmd)
    return ProcessingResult(
        output_uri=str(output_path),
        result={"mock": False, "codec": codec, "resolution": resolution},
    )


def process_thumbnail(
    input_path: Path, output_path: Path, params: dict[str, Any], use_mock: bool
) -> ProcessingResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = params.get("timestamp_seconds", 1)

    if use_mock:
        _mock_delay()
        output_path.write_bytes(b"")  # placeholder thumbnail
        return ProcessingResult(
            output_uri=str(output_path), result={"mock": True, "timestamp_seconds": timestamp}
        )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(timestamp),
        "-i", str(input_path),
        "-frames:v", "1",
        str(output_path),
    ]
    _run(cmd)
    return ProcessingResult(
        output_uri=str(output_path), result={"mock": False, "timestamp_seconds": timestamp}
    )


def process_audio_extract(
    input_path: Path, output_path: Path, params: dict[str, Any], use_mock: bool
) -> ProcessingResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio_format = params.get("format", "mp3")

    if use_mock:
        _mock_delay()
        output_path.write_bytes(b"")
        return ProcessingResult(
            output_uri=str(output_path), result={"mock": True, "format": audio_format}
        )

    cmd = ["ffmpeg", "-y", "-i", str(input_path), "-vn", "-acodec", "libmp3lame", str(output_path)]
    _run(cmd)
    return ProcessingResult(
        output_uri=str(output_path), result={"mock": False, "format": audio_format}
    )


def process_metadata(input_path: Path, params: dict[str, Any], use_mock: bool) -> ProcessingResult:
    if use_mock:
        _mock_delay()
        return ProcessingResult(
            output_uri=None,
            result={
                "mock": True,
                "format": "unknown",
                "duration_seconds": 0,
                "streams": [],
                "note": "mock ffprobe: no real ffmpeg/source file available",
            },
        )

    stdout = _run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            str(input_path),
        ]
    )
    probe = json.loads(stdout)
    fmt = probe.get("format", {})
    return ProcessingResult(
        output_uri=None,
        result={
            "mock": False,
            "format": fmt.get("format_name"),
            "duration_seconds": float(fmt.get("duration", 0) or 0),
            "streams": probe.get("streams", []),
        },
    )
