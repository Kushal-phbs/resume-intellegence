"""Prompt template for keyword extraction."""

from __future__ import annotations

from app.prompts.base import BasePrompt


class KeywordPrompt(BasePrompt):
    """Prompt builder for extracting relevant ATS keywords."""

    def build(self, **kwargs: object) -> str:
        return (
            "Extract high-signal keywords, technologies, certifications, and role "
            "terms that an ATS would likely match against."
        )
