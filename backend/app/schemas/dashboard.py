"""API schema models for dashboard and analytics endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums.analytics import ActivityType, EntityType


class ActivityResponse(BaseModel):
    """Public representation of a dashboard activity event."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    user_id: UUID
    activity_type: ActivityType
    entity_type: EntityType
    entity_id: UUID | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)
    created_at: datetime | None = None


class AnalyticsResponse(BaseModel):
    """Public representation of aggregated AI processing analytics."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    user_id: UUID
    total_ai_requests: int = Field(ge=0)
    total_tokens_used: int = Field(ge=0)
    successful_requests: int = Field(ge=0)
    failed_requests: int = Field(ge=0)
    success_rate: float = Field(ge=0, le=100)
    average_processing_time_ms: float | None = Field(default=None, ge=0)
    last_activity_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DashboardSummaryResponse(BaseModel):
    """Summarized dashboard metrics for top-level KPI widgets."""

    model_config = ConfigDict(from_attributes=True)

    total_resumes: int = Field(ge=0)
    total_resume_analyses: int = Field(ge=0)
    total_job_analyses: int = Field(ge=0)
    total_tailoring_sessions: int = Field(ge=0)
    generated_cover_letters: int = Field(ge=0)
    average_resume_score: float | None = Field(default=None, ge=0, le=100)
    average_job_match_score: float | None = Field(default=None, ge=0, le=100)
    average_tailoring_score: float | None = Field(default=None, ge=0, le=100)


class StatisticsResponse(BaseModel):
    """Extended aggregated analytics used for dashboard statistics views."""

    total_resumes: int = Field(ge=0)
    total_analyses: int = Field(ge=0)
    total_tailoring_sessions: int = Field(ge=0)
    total_exports: int = Field(ge=0)
    average_ats_score: float | None = Field(default=None, ge=0, le=100)
    average_job_match_score: float | None = Field(default=None, ge=0, le=100)
    average_tailoring_score: float | None = Field(default=None, ge=0, le=100)
    total_ai_requests: int = Field(ge=0)
    success_rate: float = Field(ge=0, le=100)
    average_processing_time_ms: float | None = Field(default=None, ge=0)
    total_tokens_used: int = Field(ge=0)


class TrendPointResponse(BaseModel):
    """Single chart point for dashboard trends."""

    timestamp: datetime
    total_resumes: int = Field(ge=0)
    total_resume_analyses: int = Field(ge=0)
    total_job_analyses: int = Field(ge=0)
    total_tailoring_sessions: int = Field(ge=0)
    generated_cover_letters: int = Field(ge=0)
    average_resume_score: float | None = Field(default=None, ge=0, le=100)
    average_job_match_score: float | None = Field(default=None, ge=0, le=100)
    average_tailoring_score: float | None = Field(default=None, ge=0, le=100)


class DashboardResponse(BaseModel):
    """Complete dashboard payload for authenticated users."""

    summary: DashboardSummaryResponse
    analytics: AnalyticsResponse
    recent_activity: list[ActivityResponse] = Field(default_factory=list)


class DashboardTrendsResponse(BaseModel):
    """Chart-friendly historical trend data."""

    points: list[TrendPointResponse] = Field(default_factory=list)
