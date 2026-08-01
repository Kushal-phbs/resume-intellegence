"""API schema models for resume tailoring endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums.tailoring import TailoringStatus


class ResumeVersionResponse(BaseModel):
    """Public representation of a tailored resume version."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Tailored resume version identifier.")
    resume_id: UUID = Field(description="Source resume identifier.")
    tailoring_session_id: UUID = Field(
        description="Parent tailoring session identifier."
    )
    professional_summary: str = Field(
        description="Generated professional summary section."
    )
    experience_json: list[dict[str, object]] = Field(
        description="Structured tailored experience section entries."
    )
    skills_json: list[dict[str, object]] = Field(
        description="Structured tailored skills section entries."
    )
    ats_score: int = Field(ge=0, le=100, description="Estimated ATS alignment score.")
    recommendations_json: list[dict[str, object]] = Field(
        description="Structured recommendations returned by tailoring pipeline."
    )
    created_at: datetime = Field(description="Record creation timestamp.")
    updated_at: datetime = Field(description="Record update timestamp.")


class CoverLetterResponse(BaseModel):
    """Public representation of a generated cover letter."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID | None = Field(default=None, description="Cover letter identifier.")
    tailoring_session_id: UUID | None = Field(
        default=None,
        description="Parent tailoring session identifier.",
    )
    title: str = Field(description="Generated cover letter title.")
    greeting: str = Field(description="Cover letter greeting line.")
    introduction: str = Field(description="Cover letter introduction paragraph.")
    body: str = Field(description="Cover letter body content.")
    closing: str = Field(description="Cover letter closing statement.")
    created_at: datetime | None = Field(default=None, description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Update timestamp.")


class TailoringSessionResponse(BaseModel):
    """Public representation of a tailoring session."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Tailoring session identifier.")
    resume_id: UUID = Field(description="Source resume identifier.")
    job_description_id: UUID = Field(description="Target job description identifier.")
    status: TailoringStatus = Field(description="Current tailoring session status.")
    created_at: datetime = Field(description="Session creation timestamp.")
    updated_at: datetime = Field(description="Session update timestamp.")


class TailoringSummaryResponse(BaseModel):
    """Summary response for create/session detail endpoints."""

    session: TailoringSessionResponse = Field(description="Tailoring session details.")
    resume_version: ResumeVersionResponse = Field(
        description="Generated tailored resume version."
    )
    cover_letter: CoverLetterResponse = Field(
        description="Generated cover letter content."
    )


class ExportResponse(BaseModel):
    """Metadata response for exported artifact downloads."""

    file_name: str = Field(description="Generated export filename.")
    format: str = Field(description="Export format (md, docx, or pdf).")
    download_path: str = Field(description="Relative download path for the export.")
