"""Resume analysis schema models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums import AnalysisStatus, SkillCategory


class SkillResponse(BaseModel):
    """Public representation of an extracted skill."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Skill record identifier.")
    analysis_id: UUID = Field(description="Parent analysis identifier.")
    skill_name: str = Field(description="Extracted skill name.")
    category: SkillCategory = Field(description="Skill category classification.")
    created_at: datetime = Field(description="Skill record creation timestamp.")
    updated_at: datetime = Field(description="Skill record update timestamp.")


class KeywordResponse(BaseModel):
    """Public representation of an extracted keyword."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Keyword record identifier.")
    analysis_id: UUID = Field(description="Parent analysis identifier.")
    keyword: str = Field(description="Extracted keyword.")
    created_at: datetime = Field(description="Keyword record creation timestamp.")
    updated_at: datetime = Field(description="Keyword record update timestamp.")


class ResumeAnalysisSummary(BaseModel):
    """Compact summary of a resume analysis run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Analysis identifier.")
    resume_id: UUID = Field(description="Resume identifier.")
    resume_version_id: UUID = Field(description="Resume version analyzed.")
    analysis_status: AnalysisStatus = Field(description="Current analysis state.")
    resume_score: int | None = Field(default=None, ge=0, le=100)
    ats_score: int | None = Field(default=None, ge=0, le=100)
    strengths: list[str] = Field(description="Detected resume strengths.")
    weaknesses: list[str] = Field(description="Detected resume weaknesses.")
    recommendations: list[str] = Field(description="Actionable improvement guidance.")
    skill_count: int = Field(ge=0, description="Total extracted skills count.")
    keyword_count: int = Field(ge=0, description="Total extracted keywords count.")
    created_at: datetime = Field(description="Analysis creation timestamp.")
    updated_at: datetime = Field(description="Last analysis update timestamp.")
    error_message: str | None = Field(
        default=None,
        description="Failure reason when status is failed.",
    )


class ResumeAnalysisSummaryResponse(ResumeAnalysisSummary):
    """Alias for API summary responses that include narrative feedback."""

    model_config = ConfigDict(from_attributes=True)


class ResumeAnalysisResponse(BaseModel):
    """Detailed representation of a stored resume analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Analysis identifier.")
    resume_id: UUID = Field(description="Resume identifier.")
    resume_version_id: UUID = Field(description="Resume version analyzed.")
    analysis_status: AnalysisStatus = Field(description="Current analysis state.")
    resume_score: int | None = Field(default=None, ge=0, le=100)
    ats_score: int | None = Field(default=None, ge=0, le=100)
    strengths: list[str] = Field(description="Detected resume strengths.")
    weaknesses: list[str] = Field(description="Detected resume weaknesses.")
    recommendations: list[str] = Field(description="Actionable improvement guidance.")
    skills: list[SkillResponse] = Field(description="Extracted skills.")
    keywords: list[KeywordResponse] = Field(description="Extracted keywords.")
    created_at: datetime = Field(description="Analysis creation timestamp.")
    updated_at: datetime = Field(description="Last analysis update timestamp.")
    error_message: str | None = Field(
        default=None,
        description="Failure reason when status is failed.",
    )
