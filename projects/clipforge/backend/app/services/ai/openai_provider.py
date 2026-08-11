"""OpenAI-backed AI provider.

Uses Whisper for transcription and a chat model for summary/chapter/tag
extraction. Imports of the ``openai`` SDK are done lazily so the package is only
required when this provider is actually selected. Any failure falls back to the
mock provider to keep the pipeline resilient.
"""

from __future__ import annotations

import json

from app.core.config import settings
from app.core.logging import get_logger
from app.services.ai.base import AnalysisResult, Chapter, TranscriptResult
from app.services.ai.mock_provider import MockAIProvider

logger = get_logger("clipforge.ai.openai")

_ANALYSIS_SYSTEM_PROMPT = (
    "You are a video content analyst. Given a transcript, respond with strict "
    "JSON containing: 'summary' (2-3 sentences), 'chapters' (array of "
    "{title, start, end} in seconds), and 'tags' (3-6 short lowercase strings)."
)


class OpenAIProvider:
    """AI provider backed by the OpenAI API."""

    name = "openai"

    def __init__(self) -> None:
        self._fallback = MockAIProvider()
        try:
            from openai import OpenAI  # noqa: PLC0415 - lazy import

            self._client = OpenAI(api_key=settings.openai_api_key)
        except Exception as exc:  # pragma: no cover - depends on optional dep
            logger.warning("openai_init_failed", extra={"error": str(exc)})
            self._client = None

    def transcribe(
        self, audio_path: str, *, duration: float | None = None
    ) -> TranscriptResult:
        if self._client is None:
            return self._fallback.transcribe(audio_path, duration=duration)
        try:
            with open(audio_path, "rb") as handle:
                result = self._client.audio.transcriptions.create(
                    model="whisper-1", file=handle
                )
            return TranscriptResult(text=getattr(result, "text", ""), language="en")
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("openai_transcribe_failed", extra={"error": str(exc)})
            return self._fallback.transcribe(audio_path, duration=duration)

    def analyze(
        self, transcript: str, *, duration: float | None = None
    ) -> AnalysisResult:
        if self._client is None:
            return self._fallback.analyze(transcript, duration=duration)
        try:
            response = self._client.chat.completions.create(
                model=settings.openai_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": _ANALYSIS_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Duration: {duration}s\nTranscript:\n{transcript}",
                    },
                ],
            )
            data = json.loads(response.choices[0].message.content or "{}")
            chapters = [
                Chapter(
                    title=str(c.get("title", "Chapter")),
                    start=float(c.get("start", 0)),
                    end=float(c.get("end", 0)),
                )
                for c in data.get("chapters", [])
            ]
            return AnalysisResult(
                summary=str(data.get("summary", "")),
                chapters=chapters,
                tags=[str(t) for t in data.get("tags", [])],
            )
        except Exception as exc:  # pragma: no cover - network path
            logger.warning("openai_analyze_failed", extra={"error": str(exc)})
            return self._fallback.analyze(transcript, duration=duration)
