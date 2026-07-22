"""Typed data transfer objects for resume tailoring."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums.tailoring import TailoringStatus


class CoverLetterDTO(BaseModel):
    """Structured cover letter content generated for a tailoring session."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str = Field(min_length=1, max_length=255)
    greeting: str = Field(min_length=1)
    introduction: str = Field(min_length=1)
    body: str = Field(min_length=1)
    closing: str = Field(min_length=1)

    @field_validator("title", "greeting", "introduction", "body", "closing")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Text fields must not be blank")
        return cleaned


class ResumeVersionDTO(BaseModel):
    """Structured tailored resume version payload."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID | None = None
    resume_id: UUID | None = None
    tailoring_session_id: UUID | None = None
    professional_summary: str = Field(min_length=1)
    experience_json: list[dict[str, object]] = Field(default_factory=list)
    skills_json: list[dict[str, object]] = Field(default_factory=list)
    ats_score: int = Field(ge=0, le=100)
    recommendations_json: list[dict[str, object]] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("professional_summary")
    @classmethod
    def _strip_summary(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("professional_summary must not be blank")
        return cleaned


class TailoringSessionDTO(BaseModel):
    """Tailoring session metadata and lifecycle state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    resume_id: UUID
    job_description_id: UUID
    status: TailoringStatus
    created_at: datetime
    updated_at: datetime


class ResumeTailoringDTO(BaseModel):
    """Final combined output returned from resume tailoring service."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    session: TailoringSessionDTO | None = None
    resume_version: ResumeVersionDTO
    cover_letter: CoverLetterDTO
