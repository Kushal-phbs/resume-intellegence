"""Prompt section for targeted resume rewrite generation."""

from __future__ import annotations

from app.prompts.base import BasePrompt


class ResumeRewritePrompt(BasePrompt):
    """Build prompt instructions for tailored resume rewriting."""

    def build(self, **kwargs: object) -> str:
        return (
            "Rewrite the resume content specifically for the target job description. "
            "Generate a professional_summary, rewritten experience with measurable "
            "achievements, ATS-focused skills alignment, and optimization "
            "recommendations. Return ONLY valid JSON. Do not include markdown. "
            "Do not include explanations."
        )
