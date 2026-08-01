"""Job analysis schema models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums import JobAnalysisStatus


class MatchedSkillResponse(BaseModel):
    """Public representation of a matched skill."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Matched-skill record identifier.")
    job_analysis_id: UUID = Field(description="Parent job analysis identifier.")
    skill_name: str = Field(
        description="Skill present in both resume and job description."
    )
    created_at: datetime = Field(description="Record creation timestamp.")
    updated_at: datetime = Field(description="Record update timestamp.")


class MissingSkillResponse(BaseModel):
    """Public representation of a missing skill."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Missing-skill record identifier.")
    job_analysis_id: UUID = Field(description="Parent job analysis identifier.")
    skill_name: str = Field(
        description="Skill required by the job but missing in resume."
    )
    created_at: datetime = Field(description="Record creation timestamp.")
    updated_at: datetime = Field(description="Record update timestamp.")


class KeywordMatchResponse(BaseModel):
    """Public representation of a matched keyword."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Keyword-match record identifier.")
    job_analysis_id: UUID = Field(description="Parent job analysis identifier.")
    keyword: str = Field(description="Matched keyword term.")
    created_at: datetime = Field(description="Record creation timestamp.")
    updated_at: datetime = Field(description="Record update timestamp.")


class JobAnalysisSummaryResponse(BaseModel):
    """Summary view of a job analysis run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Job analysis identifier.")
    resume_id: UUID = Field(description="Resume identifier.")
    job_description_id: UUID = Field(description="Job description identifier.")
    analysis_status: JobAnalysisStatus = Field(description="Current analysis state.")
    match_score: int | None = Field(default=None, ge=0, le=100)
    ats_match_score: int | None = Field(default=None, ge=0, le=100)
    strengths: list[str] = Field(
        description="Areas where resume aligns with job needs."
    )
    weaknesses: list[str] = Field(description="Detected alignment gaps.")
    recommendations: list[str] = Field(description="Suggested improvements.")
    created_at: datetime = Field(description="Analysis creation timestamp.")
    updated_at: datetime = Field(description="Last analysis update timestamp.")
    error_message: str | None = Field(
        default=None,
        description="Failure reason when analysis status is failed.",
    )


class JobAnalysisResponse(JobAnalysisSummaryResponse):
    """Detailed representation of a stored job analysis."""

    summary: str | None = Field(
        default=None,
        description="Narrative summary of the analysis outcome.",
    )
    matched_skills: list[MatchedSkillResponse] = Field(
        description="Skills that match between resume and job description."
    )
    missing_skills: list[MissingSkillResponse] = Field(
        description="Skills missing from the resume for this job."
    )
    keyword_matches: list[KeywordMatchResponse] = Field(
        description="Matched keyword terms for this analysis."
    )
