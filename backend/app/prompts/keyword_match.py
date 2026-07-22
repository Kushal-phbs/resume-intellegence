"""Prompt section for keyword alignment analysis."""

from __future__ import annotations

from app.prompts.base import BasePrompt


class KeywordMatchPrompt(BasePrompt):
    """Prompt builder for keyword overlap extraction."""

    def build(self, **kwargs: object) -> str:
        return (
            "Extract key terms from the job description that are explicitly "
            "matched in the resume. Focus on technologies, certifications, and "
            "domain-specific keywords."
        )
