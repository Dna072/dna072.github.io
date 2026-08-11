"""Deterministic mock AI provider.

Generates plausible, stable outputs without any network access so the whole
product can be demoed and tested offline. Output is seeded from the input so
repeated runs are deterministic.
"""

from __future__ import annotations

import hashlib
import random

from app.services.ai.base import AnalysisResult, Chapter, TranscriptResult

_SAMPLE_SENTENCES = [
    "Welcome back to the channel, today we are diving into something exciting.",
    "Let's start by looking at the core concepts before we go hands on.",
    "This part is where most people get tripped up, so pay close attention.",
    "Notice how the pipeline stays responsive even under heavy load.",
    "We measured latency across every stage and the results were promising.",
    "Here is a quick recap of what we covered and where to go next.",
    "Thanks for watching, and don't forget to check the description for links.",
]

_TAG_POOL = [
    "tutorial",
    "product-demo",
    "engineering",
    "walkthrough",
    "highlights",
    "interview",
    "release",
    "deep-dive",
    "behind-the-scenes",
    "announcement",
]


def _seed_from(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % (2**32)


class MockAIProvider:
    """Offline-friendly AI provider used by default in demo mode."""

    name = "mock"

    def transcribe(
        self, audio_path: str, *, duration: float | None = None
    ) -> TranscriptResult:
        rng = random.Random(_seed_from(audio_path))
        length = max(3, int((duration or 60) // 20))
        lines = [rng.choice(_SAMPLE_SENTENCES) for _ in range(length)]
        return TranscriptResult(text=" ".join(lines), language="en")

    def analyze(
        self, transcript: str, *, duration: float | None = None
    ) -> AnalysisResult:
        rng = random.Random(_seed_from(transcript))
        total = duration or 120.0

        # Build 3-4 evenly spaced chapters.
        n_chapters = rng.randint(3, 4)
        step = total / n_chapters
        chapter_titles = [
            "Introduction",
            "Core Walkthrough",
            "Deep Dive",
            "Wrap Up",
            "Q & A",
        ]
        chapters = [
            Chapter(
                title=chapter_titles[i % len(chapter_titles)],
                start=round(i * step, 2),
                end=round(min((i + 1) * step, total), 2),
            )
            for i in range(n_chapters)
        ]

        first_sentence = transcript.split(".")[0].strip() if transcript else "This video"
        summary = (
            f"{first_sentence}. The video walks through the topic across "
            f"{n_chapters} chapters, covering setup, a hands-on walkthrough, "
            "and a concise recap of the key takeaways."
        )

        tags = rng.sample(_TAG_POOL, k=rng.randint(3, 5))
        return AnalysisResult(summary=summary, chapters=chapters, tags=tags)
