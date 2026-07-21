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

    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)

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

    id: UUID
    user_id: UUID
    title: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class ResumeListResponse(BaseModel):
    """A paginated-friendly list of resumes."""

    items: list[ResumeResponse]
    total: int


class ResumeVersionResponse(BaseModel):
    """Public representation of a single resume version."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    version_number: int
    content: str
    file_path: str | None
    created_at: datetime
    updated_at: datetime


class ResumeUploadResponse(BaseModel):
    """Response returned after successfully uploading a resume."""

    resume: ResumeResponse
    version: ResumeVersionResponse
    status: ResumeStatus = ResumeStatus.ACTIVE
    file_type: ResumeFileType
