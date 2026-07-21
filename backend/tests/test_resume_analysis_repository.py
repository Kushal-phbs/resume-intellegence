from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.dto.analysis import AnalysisResult, AnalysisSkillResult
from app.enums import AnalysisStatus, SkillCategory
from app.models.resume_analysis import ResumeAnalysis
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository


def _build_repository() -> tuple[ResumeAnalysisRepository, AsyncMock]:
    session = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return ResumeAnalysisRepository(session), session


def _analysis_result() -> AnalysisResult:
    return AnalysisResult(
        ats_score=88,
        resume_score=91,
        strengths=["Clear structure"],
        weaknesses=["Could add metrics"],
        recommendations=["Quantify impact"],
        skills=[
            AnalysisSkillResult(skill_name="Python", category=SkillCategory.TECHNICAL)
        ],
        keywords=["FastAPI"],
    )


def test_create_persists_and_returns_analysis() -> None:
    repository, session = _build_repository()
    resume_id = uuid4()
    version_id = uuid4()

    analysis = asyncio.run(
        repository.create(
            resume_id=resume_id,
            resume_version_id=version_id,
            analysis_status=AnalysisStatus.PROCESSING,
        )
    )

    assert isinstance(analysis, ResumeAnalysis)
    assert analysis.resume_id == resume_id
    assert analysis.resume_version_id == version_id
    assert analysis.analysis_status == AnalysisStatus.PROCESSING.value
    session.add.assert_called_once_with(analysis)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(analysis)


def test_get_latest_returns_most_recent_analysis() -> None:
    repository, session = _build_repository()
    expected = SimpleNamespace(id=uuid4())
    result = MagicMock()
    result.scalar_one_or_none.return_value = expected
    session.execute = AsyncMock(return_value=result)

    latest = asyncio.run(repository.get_latest(uuid4()))

    assert latest is expected


def test_list_by_resume_returns_analyses() -> None:
    repository, session = _build_repository()
    expected = [SimpleNamespace(id=uuid4()), SimpleNamespace(id=uuid4())]
    result = MagicMock()
    result.scalars.return_value.all.return_value = expected
    session.execute = AsyncMock(return_value=result)

    analyses = asyncio.run(repository.list_by_resume(uuid4()))

    assert analyses == expected


def test_get_latest_completed_returns_most_recent_completed_analysis() -> None:
    repository, session = _build_repository()
    expected = SimpleNamespace(id=uuid4())
    result = MagicMock()
    result.scalar_one_or_none.return_value = expected
    session.execute = AsyncMock(return_value=result)

    latest = asyncio.run(repository.get_latest_completed(uuid4()))

    assert latest is expected


def test_get_active_by_resume_returns_processing_analysis() -> None:
    repository, session = _build_repository()
    expected = SimpleNamespace(id=uuid4())
    result = MagicMock()
    result.scalar_one_or_none.return_value = expected
    session.execute = AsyncMock(return_value=result)

    active = asyncio.run(repository.get_active_by_resume(uuid4()))

    assert active is expected


def test_update_persists_typed_result() -> None:
    repository, session = _build_repository()
    analysis = SimpleNamespace(
        id=uuid4(),
        analysis_status=AnalysisStatus.PENDING.value,
        resume_score=None,
        ats_score=None,
        strengths=[],
        weaknesses=[],
        recommendations=[],
        skills=[],
        keywords=[],
    )
    repository.get_by_id = AsyncMock(side_effect=[analysis, analysis])
    result = _analysis_result()

    updated = asyncio.run(
        repository.update(
            analysis.id,
            result=result,
            analysis_status=AnalysisStatus.COMPLETED,
            llm_model="test-model",
            raw_response="{}",
            error_message=None,
        )
    )

    assert updated is analysis
    assert analysis.analysis_status == AnalysisStatus.COMPLETED.value
    assert analysis.resume_score == 91
    assert analysis.ats_score == 88
    assert analysis.strengths == ["Clear structure"]
    assert analysis.skills[0].skill_name == "Python"
    assert analysis.keywords[0].keyword == "FastAPI"
    session.flush.assert_awaited_once()


def test_delete_returns_true_when_analysis_exists() -> None:
    repository, session = _build_repository()
    analysis = SimpleNamespace(id=uuid4())
    repository.get_by_id = AsyncMock(return_value=analysis)

    deleted = asyncio.run(repository.delete(analysis.id))

    assert deleted is True
    session.delete.assert_awaited_once_with(analysis)
    session.flush.assert_awaited_once()
