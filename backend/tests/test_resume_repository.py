from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.models.resume import Resume
from app.models.resume_version import ResumeVersion
from app.repositories.resume_repository import ResumeRepository


def _build_repository() -> tuple[ResumeRepository, AsyncMock]:
    session = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return ResumeRepository(session), session


def test_create_persists_and_returns_resume() -> None:
    repository, session = _build_repository()
    user_id = uuid4()

    resume = asyncio.run(repository.create(user_id=user_id, title="My Resume"))

    assert isinstance(resume, Resume)
    assert resume.user_id == user_id
    assert resume.title == "My Resume"
    assert resume.is_primary is False
    session.add.assert_called_once_with(resume)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(resume)


def test_get_returns_resume_when_found() -> None:
    repository, session = _build_repository()
    expected = SimpleNamespace(id=uuid4())
    result = MagicMock()
    result.scalar_one_or_none.return_value = expected
    session.execute = AsyncMock(return_value=result)

    found = asyncio.run(repository.get(expected.id))

    assert found is expected
    session.execute.assert_awaited_once()


def test_get_returns_none_when_missing() -> None:
    repository, session = _build_repository()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)

    found = asyncio.run(repository.get(uuid4()))

    assert found is None


def test_list_by_user_returns_resumes() -> None:
    repository, session = _build_repository()
    expected = [SimpleNamespace(id=uuid4()), SimpleNamespace(id=uuid4())]
    result = MagicMock()
    result.scalars.return_value.all.return_value = expected
    session.execute = AsyncMock(return_value=result)

    resumes = asyncio.run(repository.list_by_user(uuid4()))

    assert resumes == expected


def test_delete_returns_true_when_resume_exists() -> None:
    repository, session = _build_repository()
    resume_id = uuid4()
    existing = SimpleNamespace(id=resume_id)
    repository.get = AsyncMock(return_value=existing)

    deleted = asyncio.run(repository.delete(resume_id))

    assert deleted is True
    session.delete.assert_awaited_once_with(existing)
    session.flush.assert_awaited_once()


def test_delete_returns_false_when_resume_missing() -> None:
    repository, session = _build_repository()
    repository.get = AsyncMock(return_value=None)

    deleted = asyncio.run(repository.delete(uuid4()))

    assert deleted is False
    session.delete.assert_not_awaited()


def test_create_version_persists_and_returns_version() -> None:
    repository, session = _build_repository()
    resume_id = uuid4()

    version = asyncio.run(
        repository.create_version(
            resume_id=resume_id,
            version_number=1,
            content="",
            file_path="abc123.pdf",
        )
    )

    assert isinstance(version, ResumeVersion)
    assert version.resume_id == resume_id
    assert version.version_number == 1
    assert version.file_path == "abc123.pdf"
    session.add.assert_called_once_with(version)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(version)


def test_get_versions_returns_ordered_versions() -> None:
    repository, session = _build_repository()
    expected = [SimpleNamespace(version_number=1), SimpleNamespace(version_number=2)]
    result = MagicMock()
    result.scalars.return_value.all.return_value = expected
    session.execute = AsyncMock(return_value=result)

    versions = asyncio.run(repository.get_versions(uuid4()))

    assert versions == expected


def test_get_latest_version_returns_most_recent() -> None:
    repository, session = _build_repository()
    expected = SimpleNamespace(version_number=3)
    result = MagicMock()
    result.scalar_one_or_none.return_value = expected
    session.execute = AsyncMock(return_value=result)

    latest = asyncio.run(repository.get_latest_version(uuid4()))

    assert latest is expected


def test_get_latest_version_returns_none_when_no_versions() -> None:
    repository, session = _build_repository()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)

    latest = asyncio.run(repository.get_latest_version(uuid4()))

    assert latest is None
