"""Prompt template for resume review recommendations."""

from __future__ import annotations

from app.prompts.base import BasePrompt


class ResumeReviewPrompt(BasePrompt):
    """Prompt builder for generating strengths, weaknesses, and recommendations."""

    def build(self, **kwargs: object) -> str:
        return (
            "Return concise strengths, weaknesses, and recommendations that help "
            "the candidate improve the resume for both human readers and ATS systems."
        )
