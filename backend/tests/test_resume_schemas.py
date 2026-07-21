from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.enums import ResumeFileType, ResumeStatus
from app.schemas.resume import (
    ResumeListResponse,
    ResumeResponse,
    ResumeUploadMetadata,
    ResumeUploadResponse,
    ResumeVersionResponse,
)


def test_resume_upload_metadata_accepts_valid_values() -> None:
    metadata = ResumeUploadMetadata(
        filename="resume.pdf", content_type="application/pdf", size_bytes=1024
    )

    assert metadata.filename == "resume.pdf"
    assert metadata.size_bytes == 1024


def test_resume_upload_metadata_rejects_blank_filename() -> None:
    with pytest.raises(ValidationError):
        ResumeUploadMetadata(
            filename="   ", content_type="application/pdf", size_bytes=1
        )


def test_resume_upload_metadata_rejects_filename_without_extension() -> None:
    with pytest.raises(ValidationError):
        ResumeUploadMetadata(
            filename="resume", content_type="application/pdf", size_bytes=1
        )


def test_resume_upload_metadata_rejects_non_positive_size() -> None:
    with pytest.raises(ValidationError):
        ResumeUploadMetadata(
            filename="resume.pdf", content_type="application/pdf", size_bytes=0
        )


def test_resume_response_from_attributes() -> None:
    now = datetime.now(UTC)

    class _Resume:
        id = uuid4()
        user_id = uuid4()
        title = "My Resume"
        is_primary = True
        created_at = now
        updated_at = now

    response = ResumeResponse.model_validate(_Resume())

    assert response.title == "My Resume"
    assert response.is_primary is True


def test_resume_list_response_wraps_items() -> None:
    now = datetime.now(UTC)
    item = ResumeResponse(
        id=uuid4(),
        user_id=uuid4(),
        title="Resume",
        is_primary=False,
        created_at=now,
        updated_at=now,
    )

    response = ResumeListResponse(items=[item], total=1)

    assert response.total == 1
    assert response.items[0] is item


def test_resume_version_response_from_attributes() -> None:
    now = datetime.now(UTC)

    class _Version:
        id = uuid4()
        resume_id = uuid4()
        version_number = 1
        content = ""
        file_path = "abc123.pdf"
        created_at = now
        updated_at = now

    response = ResumeVersionResponse.model_validate(_Version())

    assert response.version_number == 1
    assert response.file_path == "abc123.pdf"


def test_resume_upload_response_defaults_status_to_active() -> None:
    now = datetime.now(UTC)
    resume = ResumeResponse(
        id=uuid4(),
        user_id=uuid4(),
        title="Resume",
        is_primary=False,
        created_at=now,
        updated_at=now,
    )
    version = ResumeVersionResponse(
        id=uuid4(),
        resume_id=resume.id,
        version_number=1,
        content="",
        file_path="abc123.pdf",
        created_at=now,
        updated_at=now,
    )

    response = ResumeUploadResponse(
        resume=resume, version=version, file_type=ResumeFileType.PDF
    )

    assert response.status == ResumeStatus.ACTIVE
    assert response.file_type == ResumeFileType.PDF
