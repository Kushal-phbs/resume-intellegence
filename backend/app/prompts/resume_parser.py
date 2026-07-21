"""Prompt template for resume text normalization."""

from __future__ import annotations

from app.prompts.base import BasePrompt


class ResumeParserPrompt(BasePrompt):
    """Prompt builder for turning raw resume text into normalized structure."""

    def build(self, **kwargs: object) -> str:
        return (
            "Normalize the provided resume text into clean sections, preserving "
            "job titles, dates, employers, education, certifications, and other "
            "salient details."
        )
