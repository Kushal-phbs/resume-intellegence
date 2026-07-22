"""Typed data transfer objects for job analysis results."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobAnalysisResult(BaseModel):
    """Validated job matching payload parsed from LLM output."""

    model_config = ConfigDict(frozen=True)

    overall_match: int = Field(ge=0, le=100)
    ats_match: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    keyword_matches: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    @field_validator(
        "matched_skills",
        "missing_skills",
        "keyword_matches",
        "strengths",
        "weaknesses",
        "recommendations",
    )
    @classmethod
    def _normalize_text_lists(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value and value.strip()]

    @field_validator("summary")
    @classmethod
    def _normalize_summary(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Summary must not be blank")
        return cleaned
