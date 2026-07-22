"""Prompt section for improvement recommendations."""

from __future__ import annotations

from app.prompts.base import BasePrompt


class JobRecommendationsPrompt(BasePrompt):
    """Prompt builder for job-fit strengths, weaknesses, and recommendations."""

    def build(self, **kwargs: object) -> str:
        return (
            "Return concise strengths, weaknesses, and recommendations that "
            "improve the resume's fit for the specific job description."
        )
