"""Prompt section for resume-to-job matching analysis."""

from __future__ import annotations

from app.prompts.base import BasePrompt


class JobMatchPrompt(BasePrompt):
    """Prompt builder for high-level resume vs job match scoring."""

    def build(self, **kwargs: object) -> str:
        return (
            "Compare the resume content against the job description and produce "
            "an overall match percentage and ATS match percentage from 0 to 100. "
            "Include a concise summary of why the candidate is or is not aligned."
        )
