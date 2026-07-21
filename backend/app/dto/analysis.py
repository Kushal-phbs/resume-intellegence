"""Typed data transfer objects for resume analysis results."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import SkillCategory


class AnalysisSkillResult(BaseModel):
    """Validated skill item extracted from an LLM analysis response."""

    model_config = ConfigDict(frozen=True)

    skill_name: str = Field(min_length=1, max_length=255)
    category: SkillCategory = SkillCategory.OTHER

    @field_validator("skill_name")
    @classmethod
    def _strip_skill_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Skill name must not be blank")
        return cleaned


class AnalysisResult(BaseModel):
    """Validated analysis payload produced from parsed LLM output.

    This DTO sits between response parsing and database persistence. It stores
    the typed, normalized analysis data that the service can pass directly to
    the repository layer without further JSON handling.
    """

    model_config = ConfigDict(frozen=True)

    ats_score: int = Field(ge=0, le=100)
    resume_score: int | None = Field(default=None, ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    skills: list[AnalysisSkillResult] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)

    @field_validator("strengths", "weaknesses", "recommendations", "keywords")
    @classmethod
    def _normalize_text_lists(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value and value.strip()]
