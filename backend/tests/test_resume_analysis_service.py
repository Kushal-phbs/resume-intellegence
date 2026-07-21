from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import (
    ExternalServiceException,
    ResumeNotFoundException,
    UnsupportedFileTypeException,
    ValidationException,
)
from app.dto.analysis import AnalysisResult, AnalysisSkillResult
from app.enums import AnalysisStatus, SkillCategory
from app.extractors.factory import TextExtractorFactory
from app.llm.models import LLMResponse
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.resume_analysis_service import ResumeAnalysisService
from app.storage.base import StorageProvider


class _StorageStub(StorageProvider):
    def __init__(self, content_by_key: dict[str, bytes]) -> None:
        self.content_by_key = content_by_key
        self.read_calls: list[str] = []

    def save(self, *, content: bytes, filename: str) -> str:
        raise NotImplementedError

    def read(self, storage_key: str) -> bytes:
        self.read_calls.append(storage_key)
        return self.content_by_key[storage_key]

    def delete(self, storage_key: str) -> None:
        raise NotImplementedError

    def exists(self, storage_key: str) -> bool:
        raise NotImplementedError

    def get_download_path(self, storage_key: str):
        raise NotImplementedError


class _ExtractorStub:
    def __init__(self, extracted_text: str) -> None:
        self.extracted_text = extracted_text
        self.calls: list[bytes] = []

    def extract(self, content: bytes) -> str:
        self.calls.append(content)
        return self.extracted_text


class _ExtractorFactoryStub:
    def __init__(self, extractor: _ExtractorStub) -> None:
        self.extractor = extractor
        self.calls: list[str] = []

    def get_extractor(self, file_path: str) -> _ExtractorStub:
        self.calls.append(file_path)
        return self.extractor


class _ParserStub:
    def __init__(self, result: AnalysisResult | Exception) -> None:
        self.result = result
        self.calls: list[str] = []

    def parse(self, content: str) -> AnalysisResult:
        self.calls.append(content)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class _ChatServiceStub:
    def __init__(self, response: LLMResponse) -> None:
        self.response = response
        self.requests: list[object] = []

    async def chat(self, request: object) -> LLMResponse:
        self.requests.append(request)
        return self.response


def _analysis_result() -> AnalysisResult:
    return AnalysisResult(
        ats_score=88,
        resume_score=91,
        strengths=["Clear structure"],
        weaknesses=["Few quantified results"],
        recommendations=["Add metrics"],
        skills=[
            AnalysisSkillResult(
                skill_name="Python",
                category=SkillCategory.TECHNICAL,
            )
        ],
        keywords=["FastAPI"],
    )


def _build_service(
    storage: _StorageStub,
    chat_response: LLMResponse,
    *,
    parser: _ParserStub | None = None,
    extractor_factory: _ExtractorFactoryStub | None = None,
) -> tuple[
    ResumeAnalysisService,
    AsyncMock,
    AsyncMock,
    _ChatServiceStub,
    _ExtractorStub,
    _ExtractorFactoryStub,
    _ParserStub,
]:
    resume_repository = AsyncMock(spec=ResumeRepository)
    analysis_repository = AsyncMock(spec=ResumeAnalysisRepository)
    chat_service = _ChatServiceStub(chat_response)
    extractor = _ExtractorStub("resume text")
    extractor_factory = extractor_factory or _ExtractorFactoryStub(extractor)
    parser = parser or _ParserStub(_analysis_result())
    service = ResumeAnalysisService(
        analysis_repository,
        resume_repository,
        storage,
        chat_service,
        analysis_parser=parser,
        extractor_factory=extractor_factory,
    )
    return (
        service,
        resume_repository,
        analysis_repository,
        chat_service,
        extractor,
        extractor_factory,
        parser,
    )


def _resume_and_version(
    *,
    user_id: object | None = None,
    resume_id: object | None = None,
    version_id: object | None = None,
    file_path: str = "resume.txt",
    file_content: bytes = b"resume bytes",
) -> tuple[SimpleNamespace, SimpleNamespace, _StorageStub]:
    user_id = user_id or uuid4()
    resume_id = resume_id or uuid4()
    version_id = version_id or uuid4()
    storage = _StorageStub({file_path: file_content})
    resume = SimpleNamespace(id=resume_id, user_id=user_id)
    version = SimpleNamespace(id=version_id, file_path=file_path)
    return resume, version, storage


def _analysis_row(*, resume_id: object, version_id: object) -> SimpleNamespace:
    now = datetime.now(UTC)
    analysis_id = uuid4()
    return SimpleNamespace(
        id=analysis_id,
        resume_id=resume_id,
        resume_version_id=version_id,
        analysis_status=AnalysisStatus.COMPLETED.value,
        resume_score=91,
        ats_score=88,
        strengths=["Clear structure"],
        weaknesses=["Few quantified results"],
        recommendations=["Add metrics"],
        skills=[
            SimpleNamespace(
                id=uuid4(),
                analysis_id=analysis_id,
                skill_name="Python",
                category=SkillCategory.TECHNICAL.value,
                created_at=now,
                updated_at=now,
            )
        ],
        keywords=[
            SimpleNamespace(
                id=uuid4(),
                analysis_id=analysis_id,
                keyword="FastAPI",
                created_at=now,
                updated_at=now,
            )
        ],
        created_at=now,
        updated_at=now,
        error_message=None,
    )


def test_analyze_resume_delegates_to_parser_and_extractor() -> None:
    resume_id = uuid4()
    owner_id = uuid4()
    resume, version, storage = _resume_and_version(
        user_id=owner_id,
        resume_id=resume_id,
    )
    (
        service,
        resume_repository,
        analysis_repository,
        chat_service,
        extractor,
        extractor_factory,
        parser,
    ) = _build_service(storage, LLMResponse(content="ignored", model="test-model"))
    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = version
    analysis_repository.get_active_by_resume.return_value = None
    analysis_repository.create.return_value = SimpleNamespace(id=uuid4())
    updated = _analysis_row(resume_id=resume_id, version_id=version.id)
    analysis_repository.update.return_value = updated

    response = asyncio.run(service.analyze_resume(owner_id, resume_id))

    assert response.resume_id == resume_id
    assert extractor_factory.calls == [version.file_path]
    assert extractor.calls == [b"resume bytes"]
    assert parser.calls == ["ignored"]
    assert chat_service.requests[0].prompt == "resume text"
    analysis_repository.create.assert_awaited_once()
    analysis_repository.update.assert_awaited_once()
    resume_repository.get.assert_awaited_once_with(resume_id)
    resume_repository.get_latest_version.assert_awaited_once_with(resume_id)


def test_analyze_resume_missing_resume_raises() -> None:
    resume_repository = AsyncMock(spec=ResumeRepository)
    analysis_repository = AsyncMock(spec=ResumeAnalysisRepository)
    storage = _StorageStub({"resume.txt": b"resume bytes"})
    chat_service = _ChatServiceStub(LLMResponse(content="{}"))
    service = ResumeAnalysisService(
        analysis_repository,
        resume_repository,
        storage,
        chat_service,
        analysis_parser=_ParserStub(_analysis_result()),
        extractor_factory=_ExtractorFactoryStub(_ExtractorStub("resume text")),
    )
    resume_repository.get.return_value = None

    with pytest.raises(ResumeNotFoundException):
        asyncio.run(service.analyze_resume(uuid4(), uuid4()))


def test_analyze_resume_empty_file_raises() -> None:
    resume_id = uuid4()
    owner_id = uuid4()
    resume, version, storage = _resume_and_version(
        user_id=owner_id,
        resume_id=resume_id,
    )
    parser = _ParserStub(_analysis_result())
    extractor = _ExtractorStub("")
    extractor_factory = _ExtractorFactoryStub(extractor)
    (
        service,
        resume_repository,
        analysis_repository,
        _chat_service,
        _,
        _,
        _,
    ) = _build_service(
        storage,
        LLMResponse(content="{}"),
        parser=parser,
        extractor_factory=extractor_factory,
    )
    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = version
    analysis_repository.get_active_by_resume.return_value = None

    with pytest.raises(ValidationException, match="Resume file is empty"):
        asyncio.run(service.analyze_resume(owner_id, resume_id))

    analysis_repository.create.assert_not_awaited()


def test_analyze_resume_rejects_unsupported_content() -> None:
    resume_id = uuid4()
    owner_id = uuid4()
    resume, version, storage = _resume_and_version(
        user_id=owner_id,
        file_path="resume.exe",
        resume_id=resume_id,
    )
    (
        service,
        resume_repository,
        analysis_repository,
        _chat_service,
        _,
        _,
        _,
    ) = _build_service(
        storage,
        LLMResponse(content="{}"),
        extractor_factory=TextExtractorFactory(),
    )
    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = version
    analysis_repository.get_active_by_resume.return_value = None

    with pytest.raises(UnsupportedFileTypeException):
        asyncio.run(service.analyze_resume(owner_id, resume_id))

    analysis_repository.create.assert_not_awaited()


def test_analyze_resume_invalid_llm_response_updates_failed_status() -> None:
    resume_id = uuid4()
    owner_id = uuid4()
    resume, version, storage = _resume_and_version(
        user_id=owner_id,
        resume_id=resume_id,
    )
    parser = _ParserStub(ExternalServiceException("Invalid LLM response format"))
    (
        service,
        resume_repository,
        analysis_repository,
        chat_service,
        _,
        _,
        _,
    ) = _build_service(
        storage,
        LLMResponse(content="not-json", model="test-model"),
        parser=parser,
    )
    pending = SimpleNamespace(id=uuid4())
    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = version
    analysis_repository.get_active_by_resume.return_value = None
    analysis_repository.create.return_value = pending
    analysis_repository.update.return_value = pending

    with pytest.raises(ExternalServiceException, match="Invalid LLM response format"):
        asyncio.run(service.analyze_resume(owner_id, resume_id))

    analysis_repository.update.assert_any_await(
        pending.id,
        result=AnalysisResult(ats_score=0),
        analysis_status=AnalysisStatus.FAILED,
        llm_model="test-model",
        raw_response="not-json",
        error_message="Invalid LLM response format",
    )
    assert chat_service.requests[0].prompt == "resume text"


def test_analyze_resume_rejects_duplicate_active_analysis() -> None:
    resume_id = uuid4()
    owner_id = uuid4()
    resume, version, storage = _resume_and_version(
        user_id=owner_id,
        resume_id=resume_id,
    )
    (
        service,
        resume_repository,
        analysis_repository,
        _chat_service,
        _,
        _,
        _,
    ) = _build_service(storage, LLMResponse(content="{}"))
    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = version
    analysis_repository.get_active_by_resume.return_value = SimpleNamespace(id=uuid4())

    with pytest.raises(ValidationException, match="already in progress"):
        asyncio.run(service.analyze_resume(owner_id, resume_id))
