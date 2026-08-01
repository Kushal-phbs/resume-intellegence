"""Resume request/response schema models."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import ResumeFileType, ResumeStatus


class ResumeUploadMetadata(BaseModel):
    """Structural metadata describing an incoming resume upload.

    This validates basic shape only (non-empty filename with an extension,
    a non-empty content type, and a positive size). Business rules such as
    whether the extension/content type/size are actually *allowed* are
    enforced by ``ResumeService`` using the configured settings.
    """

    filename: str = Field(
        min_length=1,
        max_length=255,
        description="Original uploaded filename including extension.",
    )
    content_type: str = Field(
        min_length=1,
        max_length=255,
        description="Client-provided MIME type for the uploaded file.",
    )
    size_bytes: int = Field(gt=0, description="Uploaded file size in bytes.")

    @field_validator("filename")
    @classmethod
    def _validate_filename_has_extension(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Filename must not be blank")
        if not Path(value).suffix:
            raise ValueError("Filename must include a file extension")
        return value


class ResumeResponse(BaseModel):
    """Public representation of a resume."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Resume identifier.")
    user_id: UUID = Field(description="Owner user identifier.")
    title: str = Field(description="Resume title.")
    is_primary: bool = Field(description="Whether this resume is marked as primary.")
    created_at: datetime = Field(description="Resume creation timestamp.")
    updated_at: datetime = Field(description="Last resume update timestamp.")


class ResumeListResponse(BaseModel):
    """A paginated-friendly list of resumes."""

    items: list[ResumeResponse] = Field(
        description="Resume items for the current page."
    )
    total: int = Field(ge=0, description="Total number of resumes available.")


class ResumeVersionResponse(BaseModel):
    """Public representation of a single resume version."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Resume version identifier.")
    resume_id: UUID = Field(description="Parent resume identifier.")
    version_number: int = Field(ge=1, description="Monotonic version number.")
    content: str = Field(description="Extracted text content for this version.")
    file_path: str | None = Field(
        default=None,
        description="Internal storage path when available.",
    )
    created_at: datetime = Field(description="Version creation timestamp.")
    updated_at: datetime = Field(description="Last version update timestamp.")


class ResumeUploadResponse(BaseModel):
    """Response returned after successfully uploading a resume."""

    resume: ResumeResponse = Field(description="Created resume record.")
    version: ResumeVersionResponse = Field(
        description="Initial stored version for the uploaded resume."
    )
    status: ResumeStatus = Field(
        default=ResumeStatus.ACTIVE,
        description="Lifecycle status assigned after upload.",
    )
    file_type: ResumeFileType = Field(description="Detected uploaded file type.")
