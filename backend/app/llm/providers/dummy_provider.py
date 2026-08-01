"""Compatibility wrapper that routes legacy DummyProvider usage to Groq."""

from __future__ import annotations

from app.llm.providers.groq_provider import GroqProvider


class DummyProvider(GroqProvider):
    """Legacy name kept for compatibility; now backed by GroqProvider."""

    pass
