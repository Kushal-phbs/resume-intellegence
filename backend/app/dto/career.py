"""Pydantic DTOs for the Career Insight feature."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SkillChangeDTO(BaseModel):
    """One skill that changed between two resume versions."""

    model_config = {"frozen": True, "extra": "forbid"}

    skill_name: str
    category: str | None = None
    evidence_resume_version_id: str | None = None
    evidence_analysis_id: str | None = None
    previous_analysis_id: str | None = None
    previous_skill_count: int = 0
    current_skill_count: int = 0
    source_snippet: str | None = None


class SkillChangesDTO(BaseModel):
    """All detected skill changes."""

    model_config = {"frozen": True, "extra": "forbid"}

    added: list[SkillChangeDTO] = Field(default_factory=list)
    strengthened: list[SkillChangeDTO] = Field(default_factory=list)
    removed: list[SkillChangeDTO] = Field(default_factory=list)


class ExperienceGrowthDTO(BaseModel):
    """An area of professional experience that grew."""

    model_config = {"frozen": True, "extra": "forbid"}

    area: str
    description: str
    evidence_resume_version_id: str | None = None
    evidence_analysis_id: str | None = None
    source_snippet: str | None = None
    related_skills: list[str] = Field(default_factory=list)


class CareerFieldDTO(BaseModel):
    """A professional field the user appears strongest in."""

    model_config = {"frozen": True, "extra": "forbid"}

    field_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_summary: str
    matching_skills: list[str] = Field(default_factory=list)
    job_analysis_ids: list[str] = Field(default_factory=list)
    tailoring_session_ids: list[str] = Field(default_factory=list)
    resume_version_ids: list[str] = Field(default_factory=list)


class StrengthDTO(BaseModel):
    """A highlighted strength backed by analysis data."""

    model_config = {"frozen": True, "extra": "forbid"}

    title: str
    description: str
    evidence_analysis_ids: list[str] = Field(default_factory=list)
    evidence_job_analysis_ids: list[str] = Field(default_factory=list)
    source_snippets: list[str] = Field(default_factory=list)


class NextOpportunityDTO(BaseModel):
    """A recommended next skill or area to develop."""

    model_config = {"frozen": True, "extra": "forbid"}

    opportunity: str
    reason: str
    priority: str = Field(default="medium", pattern=r"^(high|medium|low)$")
    evidence_job_analysis_ids: list[str] = Field(default_factory=list)
    evidence_missing_skills: list[str] = Field(default_factory=list)
    related_field: str | None = None


class CareerOverviewDTO(BaseModel):
    """One-line summary with key progression numbers."""

    model_config = {"frozen": True, "extra": "forbid"}

    latest_ats_score: int | None = None
    previous_ats_score: int | None = None
    ats_delta: int | None = None
    total_resumes_analyzed: int = 0
    total_versions_compared: int = 0
    longest_analysis_span_days: int | None = None


class CareerInsightResponse(BaseModel):
    """Top-level Career Insight response returned by the service."""

    model_config = {"frozen": True, "extra": "forbid"}

    overview: CareerOverviewDTO = Field(default_factory=CareerOverviewDTO)
    skill_changes: SkillChangesDTO = Field(default_factory=SkillChangesDTO)
    experience_growth: list[ExperienceGrowthDTO] = Field(default_factory=list)
    career_fields: list[CareerFieldDTO] = Field(default_factory=list)
    strengths: list[StrengthDTO] = Field(default_factory=list)
    next_opportunities: list[NextOpportunityDTO] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)
    data_version_pairs: int = 0


class _LlmFields(BaseModel):
    """Fields the LLM is asked to generate (non-deterministic)."""

    model_config = {"extra": "forbid"}

    experience_growth: list[ExperienceGrowthDTO] = Field(default_factory=list)
    career_fields: list[CareerFieldDTO] = Field(default_factory=list)
    strengths: list[StrengthDTO] = Field(default_factory=list)
    next_opportunities: list[NextOpportunityDTO] = Field(default_factory=list)
