from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.dto.tailoring import (
    CoverLetterDTO,
    ResumeTailoringDTO,
    ResumeVersionDTO,
    TailoringSessionDTO,
)
from app.enums.tailoring import TailoringStatus


def test_cover_letter_dto_validates_required_fields() -> None:
    dto = CoverLetterDTO(
        title="Backend Engineer Application",
        greeting="Dear Hiring Manager,",
        introduction="I am excited to apply.",
        body="I improved API latency by 40%.",
        closing="Sincerely, Candidate",
    )

    assert dto.title == "Backend Engineer Application"


def test_cover_letter_dto_rejects_blank_fields() -> None:
    with pytest.raises(ValueError):
        CoverLetterDTO(
            title="  ",
            greeting="Hi",
            introduction="Intro",
            body="Body",
            closing="Bye",
        )


def test_resume_version_dto_validates_score_range() -> None:
    with pytest.raises(ValueError):
        ResumeVersionDTO(
            professional_summary="Summary",
            experience_json=[],
            skills_json=[],
            ats_score=101,
            recommendations_json=[],
        )


def test_resume_tailoring_dto_supports_optional_session() -> None:
    resume_version = ResumeVersionDTO(
        professional_summary="Summary",
        experience_json=[],
        skills_json=[],
        ats_score=88,
        recommendations_json=[],
    )
    cover_letter = CoverLetterDTO(
        title="Title",
        greeting="Greeting",
        introduction="Intro",
        body="Body",
        closing="Closing",
    )

    dto = ResumeTailoringDTO(
        session=None,
        resume_version=resume_version,
        cover_letter=cover_letter,
    )

    assert dto.session is None


def test_tailoring_session_dto_roundtrip() -> None:
    now = datetime.now(UTC)
    dto = TailoringSessionDTO(
        id=uuid4(),
        resume_id=uuid4(),
        job_description_id=uuid4(),
        status=TailoringStatus.PROCESSING,
        created_at=now,
        updated_at=now,
    )

    assert dto.status == TailoringStatus.PROCESSING
