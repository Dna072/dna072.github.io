"""Deterministic, offline AI provider used for demo mode and tests.

Produces plausible, structured output derived from the input so the full
end-to-end product (upload -> process -> transcript/summary/chapters/tags) works
without any external API key or network access.
"""

from __future__ import annotations

import hashlib
import re

from app.services.ai.base import (
    ChapterMarker,
    ContentInsights,
    Transcript,
    TranscriptSegment,
)

_SAMPLE_SENTENCES = [
    "Welcome back to the channel, today we are diving into something exciting.",
    "Let's start by setting up the project and reviewing the core architecture.",
    "Notice how the pipeline processes each stage independently and asynchronously.",
    "This pattern keeps the system responsive even under heavy upload volume.",
    "Next, we wire up the worker so jobs are consumed from the queue reliably.",
    "Finally, we surface the results in the dashboard with live status updates.",
    "Thanks for watching, and don't forget to check the description for resources.",
]

_TAG_VOCAB = [
    "tutorial",
    "engineering",
    "backend",
    "architecture",
    "pipeline",
    "demo",
    "walkthrough",
    "python",
    "async",
    "overview",
]


class MockAIProvider:
    """A stand-in ``AIProvider`` implementation (no external calls)."""

    name = "mock"

    def transcribe(
        self, audio_path: str, *, duration_seconds: float | None = None
    ) -> Transcript:
        duration = duration_seconds or 90.0
        # Choose a stable number of segments based on duration.
        seg_count = max(3, min(len(_SAMPLE_SENTENCES), int(duration // 15) or 3))
        step = duration / seg_count
        segments: list[TranscriptSegment] = []
        for i in range(seg_count):
            start = round(i * step, 2)
            end = round(min((i + 1) * step, duration), 2)
            segments.append(
                TranscriptSegment(start=start, end=end, text=_SAMPLE_SENTENCES[i])
            )
        text = " ".join(s.text for s in segments)
        return Transcript(text=text, segments=segments, language="en")

    def analyze(
        self, transcript: str, *, title: str, duration_seconds: float | None = None
    ) -> ContentInsights:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", transcript) if s.strip()]
        summary = self._summarize(title, sentences)
        chapters = self._chapters(sentences, duration_seconds or 90.0)
        tags = self._tags(title, transcript)
        return ContentInsights(summary=summary, chapters=chapters, tags=tags)

    @staticmethod
    def _summarize(title: str, sentences: list[str]) -> str:
        head = sentences[:2] if sentences else []
        body = " ".join(head)
        return (
            f"{title} is a walkthrough covering the setup, core architecture, and an "
            f"asynchronous processing pipeline. {body}".strip()
        )

    @staticmethod
    def _chapters(sentences: list[str], duration: float) -> list[ChapterMarker]:
        if not sentences:
            return [ChapterMarker(start=0.0, title="Introduction")]
        count = min(4, len(sentences))
        step = duration / count
        titles = ["Introduction", "Setup & Architecture", "Processing Pipeline", "Wrap Up"]
        return [
            ChapterMarker(start=round(i * step, 2), title=titles[i % len(titles)])
            for i in range(count)
        ]

    @staticmethod
    def _tags(title: str, transcript: str) -> list[str]:
        # Deterministically pick tags seeded by content so results are stable.
        seed = int(hashlib.sha256((title + transcript).encode()).hexdigest(), 16)
        picked: list[str] = []
        vocab = list(_TAG_VOCAB)
        for _ in range(5):
            if not vocab:
                break
            idx = seed % len(vocab)
            picked.append(vocab.pop(idx))
            seed //= 7
        return picked
