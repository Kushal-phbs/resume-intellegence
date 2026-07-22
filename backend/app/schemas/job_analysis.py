"""Job analysis schema models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums import JobAnalysisStatus


class MatchedSkillResponse(BaseModel):
    """Public representation of a matched skill."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_analysis_id: UUID
    skill_name: str
    created_at: datetime
    updated_at: datetime


class MissingSkillResponse(BaseModel):
    """Public representation of a missing skill."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_analysis_id: UUID
    skill_name: str
    created_at: datetime
    updated_at: datetime


class KeywordMatchResponse(BaseModel):
    """Public representation of a matched keyword."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_analysis_id: UUID
    keyword: str
    created_at: datetime
    updated_at: datetime


class JobAnalysisSummaryResponse(BaseModel):
    """Summary view of a job analysis run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    job_description_id: UUID
    analysis_status: JobAnalysisStatus
    match_score: int | None = Field(default=None, ge=0, le=100)
    ats_match_score: int | None = Field(default=None, ge=0, le=100)
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None


class JobAnalysisResponse(JobAnalysisSummaryResponse):
    """Detailed representation of a stored job analysis."""

    summary: str | None = None
    matched_skills: list[MatchedSkillResponse]
    missing_skills: list[MissingSkillResponse]
    keyword_matches: list[KeywordMatchResponse]
