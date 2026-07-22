"""Prompt section for ATS optimization suggestions."""

from __future__ import annotations

from app.prompts.base import BasePrompt


class TailoringAtsPrompt(BasePrompt):
    """Build prompt instructions for ATS optimization guidance."""

    def build(self, **kwargs: object) -> str:
        return (
            "Analyze ATS alignment and provide missing keywords, optimization "
            "suggestions, and score-improvement ideas tied to the job description. "
            "Return ONLY valid JSON. Do not include markdown. Do not include "
            "explanations."
        )
