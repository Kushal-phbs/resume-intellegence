"""Prompt template for ATS analysis."""

from __future__ import annotations

from app.prompts.base import BasePrompt


class AtsPrompt(BasePrompt):
    """Prompt builder for ATS-oriented analysis."""

    def build(self, **kwargs: object) -> str:
        return (
            "Score the resume for ATS compatibility from 0 to 100. Evaluate "
            "keyword density, structure, formatting clarity, and relevance to "
            "common applicant tracking systems."
        )
