"""Resume analysis schema models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums import AnalysisStatus, SkillCategory


class SkillResponse(BaseModel):
    """Public representation of an extracted skill."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_id: UUID
    skill_name: str
    category: SkillCategory
    created_at: datetime
    updated_at: datetime


class KeywordResponse(BaseModel):
    """Public representation of an extracted keyword."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_id: UUID
    keyword: str
    created_at: datetime
    updated_at: datetime


class ResumeAnalysisSummary(BaseModel):
    """Compact summary of a resume analysis run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    resume_version_id: UUID
    analysis_status: AnalysisStatus
    resume_score: int | None = Field(default=None, ge=0, le=100)
    ats_score: int | None = Field(default=None, ge=0, le=100)
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    skill_count: int
    keyword_count: int
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None


class ResumeAnalysisSummaryResponse(ResumeAnalysisSummary):
    """Alias for API summary responses that include narrative feedback."""

    model_config = ConfigDict(from_attributes=True)


class ResumeAnalysisResponse(BaseModel):
    """Detailed representation of a stored resume analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    resume_version_id: UUID
    analysis_status: AnalysisStatus
    resume_score: int | None = Field(default=None, ge=0, le=100)
    ats_score: int | None = Field(default=None, ge=0, le=100)
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    skills: list[SkillResponse]
    keywords: list[KeywordResponse]
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None
