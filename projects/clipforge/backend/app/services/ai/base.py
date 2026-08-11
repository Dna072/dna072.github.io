"""AI provider abstraction.

The pipeline depends only on the :class:`AIProvider` protocol, never on a
concrete vendor SDK. This keeps business logic testable (via
:class:`MockAIProvider`) and lets ClipForge run in a fully functional *demo mode*
without any API key. Swapping providers is a one-line factory change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(slots=True)
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass(slots=True)
class Transcript:
    text: str
    segments: list[TranscriptSegment] = field(default_factory=list)
    language: str = "en"


@dataclass(slots=True)
class ChapterMarker:
    start: float
    title: str


@dataclass(slots=True)
class ContentInsights:
    summary: str
    chapters: list[ChapterMarker]
    tags: list[str]


@runtime_checkable
class AIProvider(Protocol):
    """Contract every AI backend (mock or real) must satisfy."""

    name: str

    def transcribe(self, audio_path: str, *, duration_seconds: float | None = None) -> Transcript:
        """Produce a transcript for the given audio track."""
        ...

    def analyze(
        self, transcript: str, *, title: str, duration_seconds: float | None = None
    ) -> ContentInsights:
        """Summarize the transcript and derive chapters + tags."""
        ...
