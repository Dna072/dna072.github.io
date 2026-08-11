"""AI provider protocol and shared result types.

The ``AIProvider`` protocol decouples the processing pipeline from any specific
model vendor. Implementations must be safe to call synchronously from a worker
process and should degrade gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class TranscriptResult:
    text: str
    language: str = "en"


@dataclass
class Chapter:
    title: str
    start: float
    end: float


@dataclass
class AnalysisResult:
    summary: str
    chapters: list[Chapter] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@runtime_checkable
class AIProvider(Protocol):
    """Contract implemented by every AI backend."""

    name: str

    def transcribe(self, audio_path: str, *, duration: float | None = None) -> TranscriptResult:
        """Produce a transcript for extracted audio."""
        ...

    def analyze(self, transcript: str, *, duration: float | None = None) -> AnalysisResult:
        """Produce a summary, chapters, and tags from a transcript."""
        ...
