from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.dto.job_analysis import JobAnalysisResult
from app.enums import JobAnalysisStatus
from app.models.job_analysis import JobAnalysis
from app.repositories.job_analysis_repository import JobAnalysisRepository


def _build_repository() -> tuple[JobAnalysisRepository, AsyncMock]:
    session = AsyncMock()
    session.add = MagicMock()
    return JobAnalysisRepository(session), session


def _analysis_result() -> JobAnalysisResult:
    return JobAnalysisResult(
        overall_match=84,
        ats_match=79,
        summary="Strong backend fit with a few cloud gaps.",
        matched_skills=["Python", "FastAPI"],
        missing_skills=["Kubernetes"],
        keyword_matches=["REST APIs"],
        strengths=["Clear API ownership"],
        weaknesses=["Limited infra detail"],
        recommendations=["Add cloud deployment results"],
    )


def test_create_persists_and_returns_job_analysis() -> None:
    repository, session = _build_repository()
    resume_id = uuid4()
    job_description_id = uuid4()

    analysis = asyncio.run(
        repository.create(
            resume_id=resume_id,
            job_description_id=job_description_id,
            analysis_status=JobAnalysisStatus.PROCESSING,
        )
    )

    assert isinstance(analysis, JobAnalysis)
    assert analysis.resume_id == resume_id
    assert analysis.job_description_id == job_description_id
    assert analysis.analysis_status == JobAnalysisStatus.PROCESSING.value
    session.add.assert_called_once_with(analysis)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(analysis)


def test_update_persists_typed_result() -> None:
    repository, session = _build_repository()
    analysis = SimpleNamespace(
        id=uuid4(),
        analysis_status=JobAnalysisStatus.PENDING.value,
        match_score=None,
        ats_match_score=None,
        summary=None,
        strengths=[],
        weaknesses=[],
        recommendations=[],
        matched_skills=[],
        missing_skills=[],
        keyword_matches=[],
    )
    repository.get_by_id = AsyncMock(side_effect=[analysis, analysis])

    updated = asyncio.run(
        repository.update(
            analysis.id,
            result=_analysis_result(),
            analysis_status=JobAnalysisStatus.COMPLETED,
            llm_model="test-model",
            raw_response="{}",
            error_message=None,
        )
    )

    assert updated is analysis
    assert analysis.analysis_status == JobAnalysisStatus.COMPLETED.value
    assert analysis.match_score == 84
    assert analysis.ats_match_score == 79
    assert analysis.summary == "Strong backend fit with a few cloud gaps."
    assert analysis.matched_skills[0].skill_name == "Python"
    assert analysis.missing_skills[0].skill_name == "Kubernetes"
    assert analysis.keyword_matches[0].keyword == "REST APIs"
    session.flush.assert_awaited_once()


def test_get_by_id_returns_analysis() -> None:
    repository, session = _build_repository()
    expected = SimpleNamespace(id=uuid4())
    result = MagicMock()
    result.scalar_one_or_none.return_value = expected
    session.execute = AsyncMock(return_value=result)

    found = asyncio.run(repository.get_by_id(uuid4()))

    assert found is expected


def test_list_by_user_uses_join_filter_without_exists_subquery() -> None:
    repository, session = _build_repository()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=result)

    asyncio.run(repository.list_by_user(uuid4()))

    statement = session.execute.await_args.args[0]
    sql = str(statement)
    assert "JOIN resumes" in sql
    assert "EXISTS" not in sql


def test_list_history_by_user_is_lightweight_and_excludes_child_eager_loads() -> None:
    repository, session = _build_repository()
    expected = [SimpleNamespace(id=uuid4())]
    result = MagicMock()
    result.scalars.return_value.all.return_value = expected
    session.execute = AsyncMock(return_value=result)

    rows = asyncio.run(repository.list_history_by_user(uuid4()))

    statement = session.execute.await_args.args[0]
    assert rows == expected
    assert "JOIN resumes" in str(statement)
    assert "EXISTS" not in str(statement)
    assert all("selectinload" not in str(option) for option in statement._with_options)


def test_persist_failed_committed_uses_independent_committed_session() -> None:
    repository, _session = _build_repository()
    analysis_id = uuid4()
    resume_id = uuid4()
    job_description_id = uuid4()

    class _SessionStub:
        def __init__(self) -> None:
            self.add = MagicMock()
            self.flush = AsyncMock()
            self.commit = AsyncMock()
            self.execute = AsyncMock(
                return_value=SimpleNamespace(
                    scalar_one_or_none=MagicMock(return_value=None)
                )
            )

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    session_stub = _SessionStub()

    def session_factory() -> _SessionStub:
        return session_stub

    repository._session_factory = session_factory  # noqa: SLF001

    asyncio.run(
        repository.persist_failed_committed(
            analysis_id=analysis_id,
            resume_id=resume_id,
            job_description_id=job_description_id,
            result=JobAnalysisResult(
                overall_match=0,
                ats_match=0,
                summary="Analysis failed",
            ),
            llm_model=None,
            raw_response=None,
            error_message="boom",
        )
    )

    session_stub.add.assert_called_once()
    session_stub.commit.assert_awaited_once()
