from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import (
    FileTooLargeException,
    ResumeNotFoundException,
    UnsupportedFileTypeException,
)
from app.enums import ResumeFileType
from app.services import resume_service as resume_service_module
from app.services.resume_service import ResumeService


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_settings = SimpleNamespace(
        resume_allowed_extensions=["pdf", "docx"],
        resume_allowed_mime_types=[
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ],
        resume_max_upload_size_bytes=1_000,
    )
    monkeypatch.setattr(resume_service_module, "settings", fake_settings)


def _build_service() -> tuple[ResumeService, AsyncMock, MagicMock]:
    resume_repository = AsyncMock()
    storage_provider = MagicMock()
    service = ResumeService(resume_repository, storage_provider)
    return service, resume_repository, storage_provider


def _pdf_response_fixtures(user_id, resume_id=None, version_id=None):
    resume_id = resume_id or uuid4()
    version_id = version_id or uuid4()
    resume = SimpleNamespace(
        id=resume_id,
        user_id=user_id,
        title="My Resume",
        is_primary=False,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    version = SimpleNamespace(
        id=version_id,
        resume_id=resume_id,
        version_number=1,
        content="",
        file_path="storage-key.pdf",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    return resume, version


def test_upload_resume_success_saves_file_and_persists_metadata() -> None:
    service, resume_repository, storage_provider = _build_service()
    user_id = uuid4()
    resume, version = _pdf_response_fixtures(user_id)

    storage_provider.save.return_value = "storage-key.pdf"
    resume_repository.create.return_value = resume
    resume_repository.create_version.return_value = version

    response = asyncio.run(
        service.upload_resume(
            user_id=user_id,
            title="My Resume",
            filename="resume.pdf",
            content_type="application/pdf",
            content=b"file-bytes",
        )
    )

    storage_provider.save.assert_called_once_with(
        content=b"file-bytes", filename="resume.pdf"
    )
    resume_repository.create.assert_awaited_once_with(
        user_id=user_id, title="My Resume"
    )
    resume_repository.create_version.assert_awaited_once_with(
        resume_id=resume.id,
        version_number=1,
        content="",
        file_path="storage-key.pdf",
    )
    assert response.file_type == ResumeFileType.PDF
    assert response.resume.id == resume.id
    assert response.version.id == version.id


def test_upload_resume_rejects_unsupported_extension() -> None:
    service, resume_repository, storage_provider = _build_service()

    with pytest.raises(UnsupportedFileTypeException):
        asyncio.run(
            service.upload_resume(
                user_id=uuid4(),
                title="My Resume",
                filename="resume.exe",
                content_type="application/pdf",
                content=b"data",
            )
        )

    storage_provider.save.assert_not_called()
    resume_repository.create.assert_not_awaited()


def test_upload_resume_rejects_unsupported_content_type() -> None:
    service, resume_repository, storage_provider = _build_service()

    with pytest.raises(UnsupportedFileTypeException):
        asyncio.run(
            service.upload_resume(
                user_id=uuid4(),
                title="My Resume",
                filename="resume.pdf",
                content_type="text/plain",
                content=b"data",
            )
        )

    storage_provider.save.assert_not_called()


def test_upload_resume_rejects_file_too_large() -> None:
    service, resume_repository, storage_provider = _build_service()

    with pytest.raises(FileTooLargeException):
        asyncio.run(
            service.upload_resume(
                user_id=uuid4(),
                title="My Resume",
                filename="resume.pdf",
                content_type="application/pdf",
                content=b"x" * 2_000,
            )
        )

    storage_provider.save.assert_not_called()


def test_upload_resume_cleans_up_storage_on_persistence_failure() -> None:
    service, resume_repository, storage_provider = _build_service()
    storage_provider.save.return_value = "storage-key.pdf"
    resume_repository.create.side_effect = RuntimeError("db down")

    with pytest.raises(RuntimeError):
        asyncio.run(
            service.upload_resume(
                user_id=uuid4(),
                title="My Resume",
                filename="resume.pdf",
                content_type="application/pdf",
                content=b"data",
            )
        )

    storage_provider.delete.assert_called_once_with("storage-key.pdf")


def test_upload_new_version_uses_next_version_number() -> None:
    service, resume_repository, storage_provider = _build_service()
    user_id = uuid4()
    resume, _ = _pdf_response_fixtures(user_id)
    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = SimpleNamespace(
        version_number=2
    )
    storage_provider.save.return_value = "storage-key-2.pdf"
    new_version = SimpleNamespace(
        id=uuid4(),
        resume_id=resume.id,
        version_number=3,
        content="",
        file_path="storage-key-2.pdf",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )
    resume_repository.create_version.return_value = new_version

    response = asyncio.run(
        service.upload_new_version(
            user_id=user_id,
            resume_id=resume.id,
            filename="resume.pdf",
            content_type="application/pdf",
            content=b"data",
        )
    )

    resume_repository.create_version.assert_awaited_once_with(
        resume_id=resume.id,
        version_number=3,
        content="",
        file_path="storage-key-2.pdf",
    )
    assert response.version_number == 3


def test_upload_new_version_raises_when_resume_not_owned() -> None:
    service, resume_repository, storage_provider = _build_service()
    resume_repository.get.return_value = SimpleNamespace(id=uuid4(), user_id=uuid4())

    with pytest.raises(ResumeNotFoundException):
        asyncio.run(
            service.upload_new_version(
                user_id=uuid4(),
                resume_id=uuid4(),
                filename="resume.pdf",
                content_type="application/pdf",
                content=b"data",
            )
        )

    storage_provider.save.assert_not_called()


def test_list_user_resumes_returns_wrapped_list() -> None:
    service, resume_repository, _ = _build_service()
    user_id = uuid4()
    resume, _ = _pdf_response_fixtures(user_id)
    resume_repository.list_by_user.return_value = [resume]

    result = asyncio.run(service.list_user_resumes(user_id))

    assert result.total == 1
    assert result.items[0].id == resume.id


def test_get_resume_returns_response_for_owner() -> None:
    service, resume_repository, _ = _build_service()
    user_id = uuid4()
    resume, _ = _pdf_response_fixtures(user_id)
    resume_repository.get.return_value = resume

    result = asyncio.run(service.get_resume(user_id=user_id, resume_id=resume.id))

    assert result.id == resume.id


def test_get_resume_returns_cached_response_without_repository_call() -> None:
    service, resume_repository, _ = _build_service()
    user_id = uuid4()
    resume_id = uuid4()

    service._cache_get = AsyncMock(
        return_value={
            "id": str(resume_id),
            "user_id": str(user_id),
            "title": "Cached Resume",
            "is_primary": False,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
    )

    result = asyncio.run(service.get_resume(user_id=user_id, resume_id=resume_id))

    assert result.id == resume_id
    assert result.title == "Cached Resume"
    resume_repository.get.assert_not_awaited()


def test_get_resume_raises_when_not_found() -> None:
    service, resume_repository, _ = _build_service()
    resume_repository.get.return_value = None

    with pytest.raises(ResumeNotFoundException):
        asyncio.run(service.get_resume(user_id=uuid4(), resume_id=uuid4()))


def test_get_resume_raises_when_not_owned() -> None:
    service, resume_repository, _ = _build_service()
    resume_repository.get.return_value = SimpleNamespace(id=uuid4(), user_id=uuid4())

    with pytest.raises(ResumeNotFoundException):
        asyncio.run(service.get_resume(user_id=uuid4(), resume_id=uuid4()))


def test_delete_resume_removes_files_and_row() -> None:
    service, resume_repository, storage_provider = _build_service()
    user_id = uuid4()
    resume, version = _pdf_response_fixtures(user_id)
    resume_repository.get.return_value = resume
    resume_repository.get_versions.return_value = [version]

    asyncio.run(service.delete_resume(user_id=user_id, resume_id=resume.id))

    storage_provider.delete.assert_called_once_with(version.file_path)
    resume_repository.delete.assert_awaited_once_with(resume.id, resume=resume)


def test_get_download_path_returns_latest_version_path() -> None:
    service, resume_repository, storage_provider = _build_service()
    user_id = uuid4()
    resume, version = _pdf_response_fixtures(user_id)
    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = version
    storage_provider.get_download_path.return_value = Path("/tmp/storage-key.pdf")

    path = asyncio.run(service.get_download_path(user_id=user_id, resume_id=resume.id))

    storage_provider.get_download_path.assert_called_once_with(version.file_path)
    assert path == Path("/tmp/storage-key.pdf")


def test_get_download_path_returns_specific_version_path() -> None:
    service, resume_repository, storage_provider = _build_service()
    user_id = uuid4()
    resume, version = _pdf_response_fixtures(user_id)
    resume_repository.get.return_value = resume
    resume_repository.get_versions.return_value = [version]
    storage_provider.get_download_path.return_value = Path("/tmp/storage-key.pdf")

    path = asyncio.run(
        service.get_download_path(
            user_id=user_id, resume_id=resume.id, version_id=version.id
        )
    )

    storage_provider.get_download_path.assert_called_once_with(version.file_path)
    assert path == Path("/tmp/storage-key.pdf")


def test_get_download_path_raises_when_version_missing() -> None:
    service, resume_repository, storage_provider = _build_service()
    user_id = uuid4()
    resume, _ = _pdf_response_fixtures(user_id)
    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = None

    with pytest.raises(ResumeNotFoundException):
        asyncio.run(service.get_download_path(user_id=user_id, resume_id=resume.id))

    storage_provider.get_download_path.assert_not_called()
