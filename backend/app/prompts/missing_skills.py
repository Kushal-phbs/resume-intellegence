"""Prompt section for missing skills extraction."""

from __future__ import annotations

from app.prompts.base import BasePrompt


class MissingSkillsPrompt(BasePrompt):
    """Prompt builder for identifying missing skills."""

    def build(self, **kwargs: object) -> str:
        return (
            "Extract missing skills that the job description expects but the "
            "resume does not clearly demonstrate. Return specific, concise "
            "skill phrases only."
        )
