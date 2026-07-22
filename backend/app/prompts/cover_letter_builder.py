"""Prompt section for cover letter generation."""

from __future__ import annotations

from app.prompts.base import BasePrompt


class CoverLetterPrompt(BasePrompt):
    """Build prompt instructions for structured cover letter output."""

    def build(self, **kwargs: object) -> str:
        return (
            "Generate a role-specific cover letter with title, greeting, "
            "introduction, body, and closing sections. Keep language professional "
            "and concrete. Return ONLY valid JSON. Do not include markdown. Do not "
            "include explanations."
        )
