from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import (
    ExternalServiceException,
    ResourceNotFoundException,
    ResumeNotFoundException,
    ValidationException,
)
from app.dto.tailoring import ResumeTailoringDTO
from app.enums.tailoring import TailoringStatus
from app.extractors.factory import TextExtractorFactory
from app.llm.models import LLMResponse
from app.repositories.cover_letter_repository import CoverLetterRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.resume_version_repository import ResumeVersionRepository
from app.repositories.tailoring_session_repository import TailoringSessionRepository
from app.services.resume_tailoring_service import ResumeTailoringService
from app.storage.base import StorageProvider


class _StorageStub(StorageProvider):
    def __init__(self, content_by_key: dict[str, bytes]) -> None:
        self.content_by_key = content_by_key

    def save(self, *, content: bytes, filename: str) -> str:
        raise NotImplementedError

    def read(self, storage_key: str) -> bytes:
        return self.content_by_key[storage_key]

    def delete(self, storage_key: str) -> None:
        raise NotImplementedError

    def exists(self, storage_key: str) -> bool:
        raise NotImplementedError

    def get_download_path(self, storage_key: str):
        raise NotImplementedError


class _ExtractorStub:
    def __init__(self, text: str) -> None:
        self.text = text

    def extract(self, _content: bytes) -> str:
        return self.text


class _ExtractorFactoryStub:
    def __init__(self, extractor: _ExtractorStub) -> None:
        self.extractor = extractor

    def get_extractor(self, _file_path: str) -> _ExtractorStub:
        return self.extractor


class _ParserStub:
    def __init__(self, result: ResumeTailoringDTO | Exception) -> None:
        self.result = result

    def parse(self, _content: str) -> ResumeTailoringDTO:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class _ChatServiceStub:
    def __init__(self, response: LLMResponse) -> None:
        self.response = response

    async def chat(self, _request: object) -> LLMResponse:
        return self.response


def _parsed_tailoring_result() -> ResumeTailoringDTO:
    return ResumeTailoringDTO.model_validate(
        {
            "session": None,
            "resume_version": {
                "professional_summary": "Summary",
                "experience_json": [],
                "skills_json": [],
                "ats_score": 84,
                "recommendations_json": [],
            },
            "cover_letter": {
                "title": "Title",
                "greeting": "Greeting",
                "introduction": "Intro",
                "body": "Body",
                "closing": "Closing",
            },
        }
    )


def _build_service(
    *,
    parser: _ParserStub | None = None,
    extractor_factory: _ExtractorFactoryStub | TextExtractorFactory | None = None,
) -> tuple[
    ResumeTailoringService,
    AsyncMock,
    AsyncMock,
    AsyncMock,
    AsyncMock,
    AsyncMock,
]:
    tailoring_session_repository = AsyncMock(spec=TailoringSessionRepository)
    resume_version_repository = AsyncMock(spec=ResumeVersionRepository)
    cover_letter_repository = AsyncMock(spec=CoverLetterRepository)
    resume_repository = AsyncMock(spec=ResumeRepository)
    job_description_repository = AsyncMock(spec=JobDescriptionRepository)
    service = ResumeTailoringService(
        tailoring_session_repository,
        resume_version_repository,
        cover_letter_repository,
        resume_repository,
        job_description_repository,
        _StorageStub({"resume.txt": b"resume bytes"}),
        _ChatServiceStub(LLMResponse(content="{}", model="test-model")),
        parser=parser or _ParserStub(_parsed_tailoring_result()),
        extractor_factory=(
            extractor_factory or _ExtractorFactoryStub(_ExtractorStub("resume text"))
        ),
    )
    return (
        service,
        tailoring_session_repository,
        resume_version_repository,
        cover_letter_repository,
        resume_repository,
        job_description_repository,
    )


def _session_row(status: TailoringStatus) -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid4(),
        resume_id=uuid4(),
        job_description_id=uuid4(),
        status=status.value,
        created_at=now,
        updated_at=now,
    )


def test_tailor_resume_success() -> None:
    (
        service,
        tailoring_session_repository,
        resume_version_repository,
        cover_letter_repository,
        resume_repository,
        job_description_repository,
    ) = _build_service()
    owner_id = uuid4()
    resume_id = uuid4()
    job_id = uuid4()
    resume_repository.get.return_value = SimpleNamespace(id=resume_id, user_id=owner_id)
    resume_repository.get_latest_version.return_value = SimpleNamespace(
        id=uuid4(), file_path="resume.txt"
    )
    job_description_repository.get.return_value = SimpleNamespace(
        id=job_id,
        user_id=owner_id,
        description="Need Python",
    )
    session = _session_row(TailoringStatus.PROCESSING)
    session.resume_id = resume_id
    session.job_description_id = job_id
    tailoring_session_repository.create.return_value = session
    updated = _session_row(TailoringStatus.COMPLETED)
    updated.id = session.id
    updated.resume_id = resume_id
    updated.job_description_id = job_id
    tailoring_session_repository.update.return_value = updated
    now = datetime.now(UTC)
    resume_version_repository.create.return_value = SimpleNamespace(
        id=uuid4(),
        resume_id=resume_id,
        tailoring_session_id=session.id,
        professional_summary="Summary",
        experience_json=[],
        skills_json=[],
        ats_score=84,
        recommendations_json=[],
        created_at=now,
        updated_at=now,
    )
    cover_letter_repository.create.return_value = SimpleNamespace(
        id=uuid4(),
        tailoring_session_id=session.id,
        title="Title",
        greeting="Greeting",
        introduction="Intro",
        body="Body",
        closing="Closing",
        created_at=now,
        updated_at=now,
    )

    result = asyncio.run(
        service.tailor_resume(
            user_id=owner_id,
            resume_id=resume_id,
            job_description_id=job_id,
        )
    )

    assert result.session is not None
    assert result.session.status == TailoringStatus.COMPLETED
    assert result.resume_version.ats_score == 84
    assert result.cover_letter.title == "Title"


def test_tailor_resume_missing_resume_raises() -> None:
    (
        service,
        _tailoring_session_repository,
        _resume_version_repository,
        _cover_letter_repository,
        resume_repository,
        _job_description_repository,
    ) = _build_service()
    resume_repository.get.return_value = None

    with pytest.raises(ResumeNotFoundException):
        asyncio.run(
            service.tailor_resume(
                user_id=uuid4(),
                resume_id=uuid4(),
                job_description_id=uuid4(),
            )
        )


def test_tailor_resume_missing_job_description_raises() -> None:
    (
        service,
        _tailoring_session_repository,
        _resume_version_repository,
        _cover_letter_repository,
        resume_repository,
        job_description_repository,
    ) = _build_service()
    owner_id = uuid4()
    resume_repository.get.return_value = SimpleNamespace(id=uuid4(), user_id=owner_id)
    resume_repository.get_latest_version.return_value = SimpleNamespace(
        id=uuid4(), file_path="resume.txt"
    )
    job_description_repository.get.return_value = None

    with pytest.raises(ResourceNotFoundException, match="Job description not found"):
        asyncio.run(
            service.tailor_resume(
                user_id=owner_id,
                resume_id=uuid4(),
                job_description_id=uuid4(),
            )
        )


def test_tailor_resume_empty_resume_raises() -> None:
    (
        service,
        _tailoring_session_repository,
        _resume_version_repository,
        _cover_letter_repository,
        resume_repository,
        job_description_repository,
    ) = _build_service(extractor_factory=_ExtractorFactoryStub(_ExtractorStub("")))
    owner_id = uuid4()
    resume_repository.get.return_value = SimpleNamespace(id=uuid4(), user_id=owner_id)
    resume_repository.get_latest_version.return_value = SimpleNamespace(
        id=uuid4(), file_path="resume.txt"
    )
    job_description_repository.get.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=owner_id,
        description="Need Python",
    )

    with pytest.raises(ValidationException, match="Resume file is empty"):
        asyncio.run(
            service.tailor_resume(
                user_id=owner_id,
                resume_id=uuid4(),
                job_description_id=uuid4(),
            )
        )


def test_tailor_resume_marks_session_failed_when_parsing_fails() -> None:
    (
        service,
        tailoring_session_repository,
        _resume_version_repository,
        _cover_letter_repository,
        resume_repository,
        job_description_repository,
    ) = _build_service(
        parser=_ParserStub(ExternalServiceException("Invalid LLM response payload"))
    )
    owner_id = uuid4()
    resume_id = uuid4()
    job_id = uuid4()
    resume_repository.get.return_value = SimpleNamespace(id=resume_id, user_id=owner_id)
    resume_repository.get_latest_version.return_value = SimpleNamespace(
        id=uuid4(), file_path="resume.txt"
    )
    job_description_repository.get.return_value = SimpleNamespace(
        id=job_id,
        user_id=owner_id,
        description="Need Python",
    )
    session = _session_row(TailoringStatus.PROCESSING)
    session.resume_id = resume_id
    session.job_description_id = job_id
    tailoring_session_repository.create.return_value = session
    tailoring_session_repository.update.return_value = session

    with pytest.raises(
        ExternalServiceException,
        match="Invalid LLM response payload",
    ):
        asyncio.run(
            service.tailor_resume(
                user_id=owner_id,
                resume_id=resume_id,
                job_description_id=job_id,
            )
        )

    tailoring_session_repository.update.assert_any_await(
        session.id,
        status=TailoringStatus.FAILED,
    )
