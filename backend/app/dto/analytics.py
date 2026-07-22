"""DTO models for dashboard analytics domain."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums.analytics import ActivityType, EntityType


class DashboardDTO(BaseModel):
    """Dashboard snapshot payload returned to callers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID | None = None
    user_id: UUID
    total_resumes: int = Field(ge=0)
    total_resume_analyses: int = Field(ge=0)
    total_job_analyses: int = Field(ge=0)
    total_tailoring_sessions: int = Field(ge=0)
    average_resume_score: float | None = Field(default=None, ge=0, le=100)
    average_job_match_score: float | None = Field(default=None, ge=0, le=100)
    average_tailoring_score: float | None = Field(default=None, ge=0, le=100)
    generated_cover_letters: int = Field(ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AnalyticsDTO(BaseModel):
    """Per-user rolling analytics counters and latency metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID | None = None
    user_id: UUID
    total_ai_requests: int = Field(ge=0)
    total_tokens_used: int = Field(ge=0)
    successful_requests: int = Field(ge=0)
    failed_requests: int = Field(ge=0)
    average_processing_time_ms: float | None = Field(default=None, ge=0)
    last_activity_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("failed_requests")
    @classmethod
    def _validate_failed_requests(cls, value: int, info):
        total = info.data.get("total_ai_requests")
        if total is not None and value > total:
            raise ValueError("failed_requests cannot exceed total_ai_requests")
        return value

    @field_validator("successful_requests")
    @classmethod
    def _validate_successful_requests(cls, value: int, info):
        total = info.data.get("total_ai_requests")
        if total is not None and value > total:
            raise ValueError("successful_requests cannot exceed total_ai_requests")
        return value


class ActivityDTO(BaseModel):
    """Activity event data used by timeline views."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID | None = None
    user_id: UUID
    activity_type: ActivityType
    entity_type: EntityType
    entity_id: UUID | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)
    created_at: datetime | None = None


class DashboardSummaryDTO(BaseModel):
    """Combined dashboard view with snapshot, analytics, and recent activity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    snapshot: DashboardDTO
    analytics: AnalyticsDTO
    recent_activity: list[ActivityDTO] = Field(default_factory=list)
