"""Parsing and validation for LLM resume analysis responses."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.core.exceptions import ExternalServiceException
from app.dto.analysis import AnalysisResult, AnalysisSkillResult
from app.enums import SkillCategory


class _ParsedAnalysisSkill(BaseModel):
    skill_name: str = Field(min_length=1, max_length=255)
    category: SkillCategory = SkillCategory.OTHER

    @field_validator("skill_name")
    @classmethod
    def _strip_skill_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Skill name must not be blank")
        return cleaned


class _ParsedAnalysisPayload(BaseModel):
    ats_score: int
    resume_score: int | None = Field(default=None, ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    skills: list[_ParsedAnalysisSkill] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)

    @field_validator("strengths", "weaknesses", "recommendations", "keywords")
    @classmethod
    def _normalize_lists(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value and value.strip()]


class AnalysisParser:
    """Parse raw LLM output into a typed :class:`AnalysisResult`.

    The parser removes code fences, validates the JSON payload structure, and
    normalizes values before any persistence logic sees the data.
    """

    _FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.DOTALL)

    def parse(self, content: str) -> AnalysisResult:
        """Parse and validate a raw LLM response string.

        Args:
            content: Raw text content returned by the LLM.

        Returns:
            A validated, normalized analysis DTO.

        Raises:
            ExternalServiceException: If the response is not valid JSON or does
                not match the expected structure.
        """
        cleaned = self._strip_code_fences(content.strip())

        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ExternalServiceException("Invalid LLM response format") from exc

        try:
            parsed = _ParsedAnalysisPayload.model_validate(payload)
        except ValidationError as exc:
            raise ExternalServiceException("Invalid LLM response payload") from exc

        return AnalysisResult(
            ats_score=self._clamp_score(parsed.ats_score),
            resume_score=parsed.resume_score,
            strengths=parsed.strengths,
            weaknesses=parsed.weaknesses,
            recommendations=parsed.recommendations,
            skills=[
                AnalysisSkillResult(
                    skill_name=skill.skill_name,
                    category=skill.category,
                )
                for skill in parsed.skills
            ],
            keywords=parsed.keywords,
        )

    def _strip_code_fences(self, content: str) -> str:
        """Remove markdown code fences commonly returned by LLMs."""
        return self._FENCE_RE.sub("", content).strip()

    def _clamp_score(self, value: int) -> int:
        """Clamp a score to the inclusive 0-100 range."""
        return max(0, min(100, value))
