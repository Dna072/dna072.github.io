"""OpenAI-backed AI provider.

Kept intentionally thin: it maps ClipForge's provider contract onto the OpenAI
SDK. Transcription uses Whisper; analysis uses a chat model constrained to JSON
output. Network calls are wrapped in retries. When no key is configured the
factory falls back to :class:`MockAIProvider`, so this class is never the reason
demo mode breaks.
"""

from __future__ import annotations

import json

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger
from app.services.ai.base import (
    ChapterMarker,
    ContentInsights,
    Transcript,
    TranscriptSegment,
)

logger = get_logger(__name__)

_ANALYSIS_SYSTEM_PROMPT = (
    "You are a video content analyst. Given a transcript, return a strict JSON "
    "object with keys: summary (string, 2-3 sentences), chapters (array of "
    "{start: number seconds, title: string}), and tags (array of 3-6 lowercase "
    "strings). Return JSON only."
)


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        from openai import OpenAI  # imported lazily so the SDK is optional at runtime

        self._client = OpenAI(api_key=api_key or settings.openai_api_key)
        self._model = model or settings.openai_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def transcribe(
        self, audio_path: str, *, duration_seconds: float | None = None
    ) -> Transcript:
        with open(audio_path, "rb") as fh:
            result = self._client.audio.transcriptions.create(
                model="whisper-1",
                file=fh,
                response_format="verbose_json",
            )
        segments = [
            TranscriptSegment(start=float(s.start), end=float(s.end), text=s.text.strip())
            for s in getattr(result, "segments", []) or []
        ]
        return Transcript(
            text=result.text,
            segments=segments,
            language=getattr(result, "language", "en") or "en",
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def analyze(
        self, transcript: str, *, title: str, duration_seconds: float | None = None
    ) -> ContentInsights:
        response = self._client.chat.completions.create(
            model=self._model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _ANALYSIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Title: {title}\nDuration: {duration_seconds}s\n\n{transcript}",
                },
            ],
        )
        payload = json.loads(response.choices[0].message.content or "{}")
        chapters = [
            ChapterMarker(start=float(c.get("start", 0)), title=str(c.get("title", "")))
            for c in payload.get("chapters", [])
        ]
        return ContentInsights(
            summary=str(payload.get("summary", "")).strip(),
            chapters=chapters,
            tags=[str(t).lower() for t in payload.get("tags", [])][:6],
        )
