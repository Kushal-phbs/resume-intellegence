"""Prompt template for skill extraction."""

from __future__ import annotations

from app.prompts.base import BasePrompt


class SkillPrompt(BasePrompt):
    """Prompt builder for extracting and classifying skills."""

    def build(self, **kwargs: object) -> str:
        return (
            "Extract the most important skills from the resume and classify each "
            "one as technical, soft, domain, tool, or other."
        )
