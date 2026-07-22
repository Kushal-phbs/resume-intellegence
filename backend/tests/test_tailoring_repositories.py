from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.enums.tailoring import TailoringStatus
from app.models.cover_letter import CoverLetter
from app.models.resume_tailoring_version import ResumeTailoringVersion
from app.models.tailoring_session import TailoringSession
from app.repositories.cover_letter_repository import CoverLetterRepository
from app.repositories.resume_version_repository import ResumeVersionRepository
from app.repositories.tailoring_session_repository import TailoringSessionRepository


def _build_session_mock() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


def test_tailoring_session_repository_create() -> None:
    session = _build_session_mock()
    repository = TailoringSessionRepository(session)

    row = asyncio.run(
        repository.create(
            resume_id=uuid4(),
            job_description_id=uuid4(),
            status=TailoringStatus.PROCESSING,
        )
    )

    assert isinstance(row, TailoringSession)
    assert row.status == TailoringStatus.PROCESSING.value
    session.add.assert_called_once_with(row)
    session.flush.assert_awaited_once()


def test_tailoring_session_repository_update_status() -> None:
    session = _build_session_mock()
    repository = TailoringSessionRepository(session)
    row = SimpleNamespace(id=uuid4(), status=TailoringStatus.PENDING.value)
    repository.get_by_id = AsyncMock(side_effect=[row, row])

    updated = asyncio.run(repository.update(row.id, status=TailoringStatus.COMPLETED))

    assert updated is row
    assert row.status == TailoringStatus.COMPLETED.value


def test_tailoring_session_repository_delete() -> None:
    session = _build_session_mock()
    repository = TailoringSessionRepository(session)
    row = SimpleNamespace(id=uuid4())
    repository.get_by_id = AsyncMock(return_value=row)

    deleted = asyncio.run(repository.delete(row.id))

    assert deleted is True
    session.delete.assert_awaited_once_with(row)


def test_resume_version_repository_create() -> None:
    session = _build_session_mock()
    repository = ResumeVersionRepository(session)

    row = asyncio.run(
        repository.create(
            resume_id=uuid4(),
            tailoring_session_id=uuid4(),
            professional_summary="Summary",
            experience_json=[],
            skills_json=[],
            ats_score=85,
            recommendations_json=[],
        )
    )

    assert isinstance(row, ResumeTailoringVersion)
    assert row.ats_score == 85


def test_resume_version_repository_update() -> None:
    session = _build_session_mock()
    repository = ResumeVersionRepository(session)
    row = SimpleNamespace(
        id=uuid4(),
        professional_summary="old",
        experience_json=[],
        skills_json=[],
        ats_score=10,
        recommendations_json=[],
    )
    repository.get_by_id = AsyncMock(side_effect=[row, row])

    updated = asyncio.run(
        repository.update(
            row.id,
            professional_summary="new",
            ats_score=95,
        )
    )

    assert updated is row
    assert row.professional_summary == "new"
    assert row.ats_score == 95


def test_cover_letter_repository_create() -> None:
    session = _build_session_mock()
    repository = CoverLetterRepository(session)

    row = asyncio.run(
        repository.create(
            tailoring_session_id=uuid4(),
            title="Title",
            greeting="Greeting",
            introduction="Intro",
            body="Body",
            closing="Closing",
        )
    )

    assert isinstance(row, CoverLetter)
    assert row.title == "Title"


def test_cover_letter_repository_update() -> None:
    session = _build_session_mock()
    repository = CoverLetterRepository(session)
    row = SimpleNamespace(id=uuid4(), title="old")
    repository.get_by_id = AsyncMock(side_effect=[row, row])

    updated = asyncio.run(repository.update(row.id, title="new"))

    assert updated is row
    assert row.title == "new"


def test_cover_letter_repository_list_by_session() -> None:
    session = _build_session_mock()
    repository = CoverLetterRepository(session)
    expected = [SimpleNamespace(id=uuid4())]
    result = MagicMock()
    result.scalars.return_value.all.return_value = expected
    session.execute = AsyncMock(return_value=result)

    rows = asyncio.run(repository.list_by_session(uuid4()))

    assert rows == expected
