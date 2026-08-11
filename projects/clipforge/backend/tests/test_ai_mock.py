from __future__ import annotations

from app.services.ai.base import AIProvider, ContentInsights, Transcript
from app.services.ai.factory import get_ai_provider
from app.services.ai.mock import MockAIProvider


def test_mock_provider_satisfies_protocol():
    provider = MockAIProvider()
    assert isinstance(provider, AIProvider)


def test_factory_defaults_to_mock(monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "ai_provider", "mock", raising=False)
    provider = get_ai_provider()
    assert provider.name == "mock"


def test_transcribe_produces_segments():
    transcript = MockAIProvider().transcribe("audio.wav", duration_seconds=90)
    assert isinstance(transcript, Transcript)
    assert transcript.text
    assert len(transcript.segments) >= 3
    assert transcript.segments[0].start == 0.0


def test_analyze_produces_summary_chapters_tags():
    provider = MockAIProvider()
    transcript = provider.transcribe("audio.wav", duration_seconds=120)
    insights = provider.analyze(transcript.text, title="My Demo", duration_seconds=120)
    assert isinstance(insights, ContentInsights)
    assert insights.summary
    assert "My Demo" in insights.summary
    assert 1 <= len(insights.chapters) <= 4
    assert 1 <= len(insights.tags) <= 6


def test_tags_are_deterministic():
    provider = MockAIProvider()
    t = provider.transcribe("a", duration_seconds=60).text
    first = provider.analyze(t, title="Same", duration_seconds=60).tags
    second = provider.analyze(t, title="Same", duration_seconds=60).tags
    assert first == second
