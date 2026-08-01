from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import anyio
import pytest

from app.core.exceptions import (
    ExternalServiceException,
    ResourceNotFoundException,
    ResumeNotFoundException,
    UnsupportedFileTypeException,
    ValidationException,
)
from app.dto.job_analysis import JobAnalysisResult
from app.enums import JobAnalysisStatus
from app.extractors.factory import TextExtractorFactory
from app.llm.models import LLMResponse
from app.repositories.job_analysis_repository import JobAnalysisRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.job_analysis_service import JobAnalysisService
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
        self.calls: list[str] = []

    def get_extractor(self, file_path: str) -> _ExtractorStub:
        self.calls.append(file_path)
        return self.extractor


class _ParserStub:
    def __init__(self, result: JobAnalysisResult | Exception) -> None:
        self.result = result
        self.calls: list[str] = []

    def parse(self, content: str) -> JobAnalysisResult:
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


def _analysis_result() -> JobAnalysisResult:
    return JobAnalysisResult(
        overall_match=86,
        ats_match=81,
        summary="Strong backend fit.",
        matched_skills=["Python", "FastAPI"],
        missing_skills=["Kubernetes"],
        keyword_matches=["REST APIs"],
        strengths=["Relevant backend ownership"],
        weaknesses=["Limited infra depth"],
        recommendations=["Add cloud deployment metrics"],
    )


def _build_service(
    storage: _StorageStub,
    chat_response: LLMResponse,
    *,
    parser: _ParserStub | None = None,
    extractor_factory: _ExtractorFactoryStub | None = None,
) -> tuple[
    JobAnalysisService,
    AsyncMock,
    AsyncMock,
    AsyncMock,
    _ChatServiceStub,
    _ParserStub,
    _ExtractorFactoryStub,
]:
    job_analysis_repository = AsyncMock(spec=JobAnalysisRepository)
    resume_repository = AsyncMock(spec=ResumeRepository)
    job_description_repository = AsyncMock(spec=JobDescriptionRepository)
    chat_service = _ChatServiceStub(chat_response)
    extractor_factory = extractor_factory or _ExtractorFactoryStub(
        _ExtractorStub("resume text")
    )
    parser = parser or _ParserStub(_analysis_result())
    service = JobAnalysisService(
        job_analysis_repository,
        resume_repository,
        job_description_repository,
        storage,
        chat_service,
        parser=parser,
        extractor_factory=extractor_factory,
    )
    return (
        service,
        job_analysis_repository,
        resume_repository,
        job_description_repository,
        chat_service,
        parser,
        extractor_factory,
    )


def test_analyze_job_match_success() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    job_description_id = uuid4()
    resume = SimpleNamespace(id=resume_id, user_id=user_id)
    version = SimpleNamespace(id=uuid4(), file_path="resume.txt")
    job_description = SimpleNamespace(
        id=job_description_id,
        user_id=user_id,
        description="Need Python and FastAPI",
    )
    storage = _StorageStub({"resume.txt": b"resume bytes"})
    (
        service,
        job_analysis_repository,
        resume_repository,
        job_description_repository,
        chat_service,
        parser,
        extractor_factory,
    ) = _build_service(storage, LLMResponse(content="ignored", model="test-model"))
    pending = SimpleNamespace(id=uuid4())
    now = datetime.now(UTC)
    updated = SimpleNamespace(
        id=uuid4(),
        resume_id=resume_id,
        job_description_id=job_description_id,
        analysis_status=JobAnalysisStatus.COMPLETED.value,
        match_score=86,
        ats_match_score=81,
        summary="Strong backend fit.",
        strengths=["Relevant backend ownership"],
        weaknesses=["Limited infra depth"],
        recommendations=["Add cloud deployment metrics"],
        matched_skills=[],
        missing_skills=[],
        keyword_matches=[],
        created_at=now,
        updated_at=now,
        error_message=None,
    )

    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = version
    job_description_repository.get.return_value = job_description
    job_analysis_repository.create.return_value = pending
    job_analysis_repository.update.return_value = updated

    result = asyncio.run(
        service.analyze_job_match(
            user_id=user_id,
            resume_id=resume_id,
            job_description_id=job_description_id,
        )
    )

    assert result.id == updated.id
    assert result.resume_id == resume_id
    assert result.job_description_id == job_description_id
    assert result.analysis_status == JobAnalysisStatus.COMPLETED
    assert result.match_score == 86
    assert result.ats_match_score == 81
    assert extractor_factory.calls == ["resume.txt"]
    assert chat_service.requests[0].max_tokens == 2048
    assert parser.calls == ["ignored"]
    job_analysis_repository.create.assert_awaited_once()
    job_analysis_repository.update.assert_awaited_once()


def test_analyze_job_match_rejects_empty_resume() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    job_description_id = uuid4()
    resume = SimpleNamespace(id=resume_id, user_id=user_id)
    version = SimpleNamespace(id=uuid4(), file_path="resume.txt")
    job_description = SimpleNamespace(
        id=job_description_id,
        user_id=user_id,
        description="Role text",
    )
    extractor_factory = _ExtractorFactoryStub(_ExtractorStub(""))
    (
        service,
        job_analysis_repository,
        resume_repository,
        job_description_repository,
        _chat_service,
        _parser,
        _extractor_factory,
    ) = _build_service(
        _StorageStub({"resume.txt": b"resume bytes"}),
        LLMResponse(content="{}"),
        extractor_factory=extractor_factory,
    )

    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = version
    job_description_repository.get.return_value = job_description

    with pytest.raises(ValidationException, match="Resume file is empty"):
        asyncio.run(
            service.analyze_job_match(
                user_id=user_id,
                resume_id=resume_id,
                job_description_id=job_description_id,
            )
        )

    job_analysis_repository.create.assert_not_awaited()


def test_analyze_job_match_rejects_empty_job_description() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    job_description_id = uuid4()
    resume = SimpleNamespace(id=resume_id, user_id=user_id)
    version = SimpleNamespace(id=uuid4(), file_path="resume.txt")
    job_description = SimpleNamespace(
        id=job_description_id,
        user_id=user_id,
        description="  ",
    )
    (
        service,
        job_analysis_repository,
        resume_repository,
        job_description_repository,
        _chat_service,
        _parser,
        _extractor_factory,
    ) = _build_service(
        _StorageStub({"resume.txt": b"resume bytes"}),
        LLMResponse(content="{}"),
    )

    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = version
    job_description_repository.get.return_value = job_description

    with pytest.raises(ValidationException, match="Job description is empty"):
        asyncio.run(
            service.analyze_job_match(
                user_id=user_id,
                resume_id=resume_id,
                job_description_id=job_description_id,
            )
        )

    job_analysis_repository.create.assert_not_awaited()


def test_analyze_job_match_handles_malformed_llm_output() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    job_description_id = uuid4()
    resume = SimpleNamespace(id=resume_id, user_id=user_id)
    version = SimpleNamespace(id=uuid4(), file_path="resume.txt")
    job_description = SimpleNamespace(
        id=job_description_id,
        user_id=user_id,
        description="Need Python",
    )
    parser = _ParserStub(ExternalServiceException("Invalid LLM response format"))
    (
        service,
        job_analysis_repository,
        resume_repository,
        job_description_repository,
        _chat_service,
        _parser,
        _extractor_factory,
    ) = _build_service(
        _StorageStub({"resume.txt": b"resume bytes"}),
        LLMResponse(content="not-json", model="test-model"),
        parser=parser,
    )
    pending = SimpleNamespace(id=uuid4())

    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = version
    job_description_repository.get.return_value = job_description
    job_analysis_repository.create.return_value = pending
    job_analysis_repository.persist_failed_committed.return_value = None

    with pytest.raises(ExternalServiceException, match="Invalid LLM response format"):
        asyncio.run(
            service.analyze_job_match(
                user_id=user_id,
                resume_id=resume_id,
                job_description_id=job_description_id,
            )
        )

    job_analysis_repository.persist_failed_committed.assert_awaited_once_with(
        analysis_id=pending.id,
        resume_id=resume_id,
        job_description_id=job_description_id,
        result=JobAnalysisResult(
            overall_match=0,
            ats_match=0,
            summary="Analysis failed",
        ),
        llm_model="test-model",
        raw_response="not-json",
        error_message="Invalid LLM response format",
    )


def test_analyze_job_match_uses_thread_offload_for_extraction(monkeypatch) -> None:
    user_id = uuid4()
    resume_id = uuid4()
    job_description_id = uuid4()
    resume = SimpleNamespace(id=resume_id, user_id=user_id)
    version = SimpleNamespace(id=uuid4(), file_path="resume.txt")
    job_description = SimpleNamespace(
        id=job_description_id,
        user_id=user_id,
        description="Need Python and FastAPI",
    )
    storage = _StorageStub({"resume.txt": b"resume bytes"})
    (
        service,
        job_analysis_repository,
        resume_repository,
        job_description_repository,
        _chat_service,
        _parser,
        _extractor_factory,
    ) = _build_service(storage, LLMResponse(content="{}"))

    run_sync_spy = AsyncMock(return_value="resume text")
    monkeypatch.setattr(anyio.to_thread, "run_sync", run_sync_spy)

    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = version
    job_description_repository.get.return_value = job_description
    job_analysis_repository.create.return_value = SimpleNamespace(id=uuid4())
    now = datetime.now(UTC)
    job_analysis_repository.update.return_value = SimpleNamespace(
        id=uuid4(),
        resume_id=resume_id,
        job_description_id=job_description_id,
        analysis_status=JobAnalysisStatus.COMPLETED.value,
        match_score=86,
        ats_match_score=81,
        summary="Strong backend fit.",
        strengths=[],
        weaknesses=[],
        recommendations=[],
        matched_skills=[],
        missing_skills=[],
        keyword_matches=[],
        created_at=now,
        updated_at=now,
        error_message=None,
    )

    asyncio.run(
        service.analyze_job_match(
            user_id=user_id,
            resume_id=resume_id,
            job_description_id=job_description_id,
        )
    )

    run_sync_spy.assert_awaited_once()


def test_list_history_uses_optimized_repository_query() -> None:
    user_id = uuid4()
    now = datetime.now(UTC)
    (
        service,
        job_analysis_repository,
        _resume_repository,
        _job_description_repository,
        _chat_service,
        _parser,
        _extractor_factory,
    ) = _build_service(
        _StorageStub({"resume.txt": b"resume bytes"}),
        LLMResponse(content="{}"),
    )

    job_analysis_repository.list_history_by_user.return_value = [
        SimpleNamespace(
            id=uuid4(),
            resume_id=uuid4(),
            job_description_id=uuid4(),
            analysis_status=JobAnalysisStatus.COMPLETED.value,
            match_score=90,
            ats_match_score=88,
            strengths=["A"],
            weaknesses=["B"],
            recommendations=["C"],
            created_at=now,
            updated_at=now,
            error_message=None,
        )
    ]

    result = asyncio.run(service.list_history(user_id=user_id))

    assert len(result) == 1
    job_analysis_repository.list_history_by_user.assert_awaited_once_with(user_id)
    job_analysis_repository.list_by_user.assert_not_called()


def test_get_analysis_returns_cached_response_without_repository_call() -> None:
    user_id = uuid4()
    analysis_id = uuid4()
    now = datetime.now(UTC)
    (
        service,
        job_analysis_repository,
        _resume_repository,
        _job_description_repository,
        _chat_service,
        _parser,
        _extractor_factory,
    ) = _build_service(
        _StorageStub({"resume.txt": b"resume bytes"}),
        LLMResponse(content="{}"),
    )

    service._cache_get = AsyncMock(
        return_value={
            "id": str(analysis_id),
            "resume_id": str(uuid4()),
            "job_description_id": str(uuid4()),
            "analysis_status": JobAnalysisStatus.COMPLETED.value,
            "match_score": 80,
            "ats_match_score": 78,
            "summary": "cached",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "matched_skills": [],
            "missing_skills": [],
            "keyword_matches": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "error_message": None,
        }
    )

    result = asyncio.run(service.get_analysis(user_id=user_id, analysis_id=analysis_id))

    assert result.id == analysis_id
    assert result.summary == "cached"
    job_analysis_repository.get_by_id.assert_not_awaited()


def test_build_system_prompt_enforces_json_only_response() -> None:
    (
        service,
        _job_analysis_repository,
        _resume_repository,
        _job_description_repository,
        _chat_service,
        _parser,
        _extractor_factory,
    ) = _build_service(
        _StorageStub({"resume.txt": b"resume bytes"}),
        LLMResponse(content="{}"),
    )

    prompt = service._build_system_prompt()

    assert "Return ONLY valid JSON" in prompt
    assert "Do not include markdown" in prompt
    assert '"overall_match"' in prompt
    assert '"recommendations"' in prompt


def test_analyze_job_match_rejects_unsupported_resume_type() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    job_description_id = uuid4()
    resume = SimpleNamespace(id=resume_id, user_id=user_id)
    version = SimpleNamespace(id=uuid4(), file_path="resume.exe")
    job_description = SimpleNamespace(
        id=job_description_id,
        user_id=user_id,
        description="Need Python",
    )
    (
        service,
        job_analysis_repository,
        resume_repository,
        job_description_repository,
        _chat_service,
        _parser,
        _extractor_factory,
    ) = _build_service(
        _StorageStub({"resume.exe": b"resume bytes"}),
        LLMResponse(content="{}"),
        extractor_factory=TextExtractorFactory(),
    )

    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = version
    job_description_repository.get.return_value = job_description

    with pytest.raises(UnsupportedFileTypeException):
        asyncio.run(
            service.analyze_job_match(
                user_id=user_id,
                resume_id=resume_id,
                job_description_id=job_description_id,
            )
        )

    job_analysis_repository.create.assert_not_awaited()


def test_analyze_job_match_missing_job_description_raises() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    job_description_id = uuid4()
    resume = SimpleNamespace(id=resume_id, user_id=user_id)
    version = SimpleNamespace(id=uuid4(), file_path="resume.txt")
    (
        service,
        _job_analysis_repository,
        resume_repository,
        job_description_repository,
        _chat_service,
        _parser,
        _extractor_factory,
    ) = _build_service(
        _StorageStub({"resume.txt": b"resume bytes"}),
        LLMResponse(content="{}"),
    )

    resume_repository.get.return_value = resume
    resume_repository.get_latest_version.return_value = version
    job_description_repository.get.return_value = None

    with pytest.raises(ResourceNotFoundException, match="Job description not found"):
        asyncio.run(
            service.analyze_job_match(
                user_id=user_id,
                resume_id=resume_id,
                job_description_id=job_description_id,
            )
        )


def test_analyze_job_match_missing_resume_raises() -> None:
    user_id = uuid4()
    (
        service,
        _job_analysis_repository,
        resume_repository,
        _job_description_repository,
        _chat_service,
        _parser,
        _extractor_factory,
    ) = _build_service(
        _StorageStub({"resume.txt": b"resume bytes"}),
        LLMResponse(content="{}"),
    )
    resume_repository.get.return_value = None

    with pytest.raises(ResumeNotFoundException):
        asyncio.run(
            service.analyze_job_match(
                user_id=user_id,
                resume_id=uuid4(),
                job_description_id=uuid4(),
            )
        )
