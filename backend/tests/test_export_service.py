from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.repositories.cover_letter_repository import CoverLetterRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.resume_version_repository import ResumeVersionRepository
from app.services.export_service import ExportService
from app.storage.base import StorageProvider


class _StorageStub(StorageProvider):
    def __init__(self, download_path: Path) -> None:
        self.download_path = download_path
        self.saved: list[tuple[bytes, str]] = []

    def save(self, *, content: bytes, filename: str) -> str:
        self.saved.append((content, filename))
        return "exports/key.md"

    def read(self, storage_key: str) -> bytes:
        raise NotImplementedError

    def delete(self, storage_key: str) -> None:
        raise NotImplementedError

    def exists(self, storage_key: str) -> bool:
        raise NotImplementedError

    def get_download_path(self, storage_key: str) -> Path:
        _ = storage_key
        return self.download_path


def _build_service(
    tmp_path: Path,
) -> tuple[
    ExportService,
    AsyncMock,
    AsyncMock,
    AsyncMock,
    _StorageStub,
]:
    resume_version_repository = AsyncMock(spec=ResumeVersionRepository)
    cover_letter_repository = AsyncMock(spec=CoverLetterRepository)
    resume_repository = AsyncMock(spec=ResumeRepository)
    storage = _StorageStub(tmp_path / "exported.md")
    service = ExportService(
        resume_version_repository,
        cover_letter_repository,
        resume_repository,
        storage,
    )
    return (
        service,
        resume_version_repository,
        cover_letter_repository,
        resume_repository,
        storage,
    )


def test_export_resume_markdown_success(tmp_path: Path) -> None:
    (
        service,
        resume_versions,
        _cover_letters,
        resumes,
        storage,
    ) = _build_service(tmp_path)
    owner_id = uuid4()
    resume_id = uuid4()
    version_id = uuid4()

    resume_versions.get_by_id.return_value = SimpleNamespace(
        id=version_id,
        resume_id=resume_id,
        professional_summary="Summary",
        experience_json=[{"text": "Built APIs"}],
        skills_json=[{"name": "Python"}],
        ats_score=90,
        recommendations_json=[{"text": "Add metrics"}],
    )
    resumes.get.return_value = SimpleNamespace(id=resume_id, user_id=owner_id)

    path = asyncio.run(
        service.export_resume(
            user_id=owner_id,
            version_id=version_id,
            format="md",
        )
    )

    assert path == storage.download_path
    assert storage.saved
    assert b"Tailored Resume" in storage.saved[0][0]


def test_export_resume_invalid_format_raises(tmp_path: Path) -> None:
    (
        service,
        resume_versions,
        _cover_letters,
        resumes,
        _storage,
    ) = _build_service(tmp_path)
    owner_id = uuid4()
    resume_id = uuid4()
    version_id = uuid4()

    resume_versions.get_by_id.return_value = SimpleNamespace(
        id=version_id,
        resume_id=resume_id,
        professional_summary="Summary",
        experience_json=[],
        skills_json=[],
        ats_score=75,
        recommendations_json=[],
    )
    resumes.get.return_value = SimpleNamespace(id=resume_id, user_id=owner_id)

    with pytest.raises(ValidationException, match="Unsupported export format"):
        asyncio.run(
            service.export_resume(
                user_id=owner_id,
                version_id=version_id,
                format="exe",
            )
        )


def test_export_resume_missing_version_raises(tmp_path: Path) -> None:
    (
        service,
        resume_versions,
        _cover_letters,
        _resumes,
        _storage,
    ) = _build_service(tmp_path)
    resume_versions.get_by_id.return_value = None

    with pytest.raises(
        ResourceNotFoundException,
        match="Tailored resume version not found",
    ):
        asyncio.run(
            service.export_resume(
                user_id=uuid4(),
                version_id=uuid4(),
                format="md",
            )
        )


def test_export_cover_letter_ownership_enforced(tmp_path: Path) -> None:
    (
        service,
        _resume_versions,
        cover_letters,
        resumes,
        _storage,
    ) = _build_service(tmp_path)
    owner_id = uuid4()
    other_user_id = uuid4()
    resume_id = uuid4()
    cover_letter_id = uuid4()

    cover_letters.get_by_id.return_value = SimpleNamespace(
        id=cover_letter_id,
        title="Title",
        greeting="Hello",
        introduction="Intro",
        body="Body",
        closing="Closing",
        tailoring_session=SimpleNamespace(resume_id=resume_id),
    )
    resumes.get.return_value = SimpleNamespace(id=resume_id, user_id=owner_id)

    with pytest.raises(ResourceNotFoundException, match="Export not found"):
        asyncio.run(
            service.export_cover_letter(
                user_id=other_user_id,
                cover_letter_id=cover_letter_id,
                format="md",
            )
        )
