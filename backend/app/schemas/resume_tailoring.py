"""API schema models for resume tailoring endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums.tailoring import TailoringStatus


class ResumeVersionResponse(BaseModel):
    """Public representation of a tailored resume version."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    tailoring_session_id: UUID
    professional_summary: str
    experience_json: list[dict[str, object]]
    skills_json: list[dict[str, object]]
    ats_score: int = Field(ge=0, le=100)
    recommendations_json: list[dict[str, object]]
    created_at: datetime
    updated_at: datetime


class CoverLetterResponse(BaseModel):
    """Public representation of a generated cover letter."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = None
    tailoring_session_id: UUID | None = None
    title: str
    greeting: str
    introduction: str
    body: str
    closing: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TailoringSessionResponse(BaseModel):
    """Public representation of a tailoring session."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    job_description_id: UUID
    status: TailoringStatus
    created_at: datetime
    updated_at: datetime


class TailoringSummaryResponse(BaseModel):
    """Summary response for create/session detail endpoints."""

    session: TailoringSessionResponse
    resume_version: ResumeVersionResponse
    cover_letter: CoverLetterResponse


class ExportResponse(BaseModel):
    """Metadata response for exported artifact downloads."""

    file_name: str
    format: str
    download_path: str
