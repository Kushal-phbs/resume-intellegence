"""Focused tests for Career Insight service, parser, and DTOs."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.dto.career import (
    CareerFieldDTO,
    CareerInsightResponse,
    CareerOverviewDTO,
    ExperienceGrowthDTO,
    NextOpportunityDTO,
    SkillChangeDTO,
    SkillChangesDTO,
    StrengthDTO,
)
from app.parsers.career_insight_parser import CareerInsightParser
from app.services.career_insight_service import (
    CareerInsightService,
    _find_skill_snippet,
    _format_skill_changes,
)

# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def parser() -> CareerInsightParser:
    return CareerInsightParser()


def _make_uuid(seed: int = 1) -> UUID:
    return UUID(f"00000000-0000-0000-0000-{seed:012d}")


def _mock_analysis(
    *,
    analysis_id: UUID,
    resume_id: UUID,
    version_id: UUID,
    ats_score: int | None = 75,
    status: str = "completed",
    skills: list[tuple[str, str]] | None = None,
    strengths: list[str] | None = None,
    weaknesses: list[str] | None = None,
    recommendations: list[str] | None = None,
    created_at: datetime | None = None,
):
    """Create a mock ResumeAnalysis object."""
    mock = MagicMock()
    mock.id = analysis_id
    mock.resume_id = resume_id
    mock.resume_version_id = version_id
    mock.ats_score = ats_score
    mock.analysis_status = status
    mock.strengths = strengths or []
    mock.weaknesses = weaknesses or []
    mock.recommendations = recommendations or []
    mock.created_at = created_at or datetime.now(timezone.utc)
    mock.extracted_text = "Some extracted text"

    skill_mocks = []
    for name, cat in skills or []:
        s = MagicMock()
        s.skill_name = name
        s.category = cat
        skill_mocks.append(s)
    mock.skills = skill_mocks
    return mock


def _mock_version(
    *, version_id: UUID, resume_id: UUID, version_number: int = 1, content: str = ""
):
    mock = MagicMock()
    mock.id = version_id
    mock.resume_id = resume_id
    mock.version_number = version_number
    mock.content = content
    mock.file_path = "some/path.pdf"
    return mock


def _mock_resume(*, resume_id: UUID, versions: list | None = None):
    mock = MagicMock()
    mock.id = resume_id
    mock.user_id = _make_uuid(99)
    mock.title = "Test Resume"
    mock.versions = versions or []
    return mock


def _mock_job_analysis(
    *,
    ja_id: UUID,
    resume_id: UUID,
    match_score: int | None = 80,
    ats_match_score: int | None = 70,
    matched_skills: list[str] | None = None,
    missing_skills: list[str] | None = None,
):
    mock = MagicMock()
    mock.id = ja_id
    mock.resume_id = resume_id
    mock.match_score = match_score
    mock.ats_match_score = ats_match_score
    mock.matched_skills = [MagicMock(skill_name=s) for s in (matched_skills or [])]
    mock.missing_skills = [MagicMock(skill_name=s) for s in (missing_skills or [])]
    mock.job_description = MagicMock(title="Software Engineer")
    return mock


def _mock_tailoring(*, session_id: UUID, resume_id: UUID):
    mock = MagicMock()
    mock.id = session_id
    mock.resume_id = resume_id
    mock.job_description = MagicMock(title="Backend Engineer")
    return mock


# ── DTO Tests ─────────────────────────────────────────────────────────────


class TestDTOs:
    def test_skill_change_dto_valid(self):
        dto = SkillChangeDTO(
            skill_name="Python",
            category="technical",
            previous_skill_count=1,
            current_skill_count=3,
        )
        assert dto.skill_name == "Python"
        assert dto.previous_skill_count == 1
        assert dto.current_skill_count == 3

    def test_skill_change_dto_extra_forbidden(self):
        with pytest.raises(ValidationError):
            SkillChangeDTO(skill_name="Python", extra_field="bad")  # type: ignore[call-arg]

    def test_career_insight_response_defaults(self):
        resp = CareerInsightResponse()
        assert resp.overview.total_resumes_analyzed == 0
        assert resp.skill_changes.added == []
        assert resp.experience_growth == []
        assert resp.career_fields == []
        assert resp.data_version_pairs == 0

    def test_career_overview_dto(self):
        dto = CareerOverviewDTO(
            latest_ats_score=85,
            previous_ats_score=72,
            ats_delta=13,
            total_resumes_analyzed=2,
        )
        assert dto.ats_delta == 13
        assert dto.latest_ats_score == 85

    def test_career_field_dto_confidence_range(self):
        with pytest.raises(ValidationError):
            CareerFieldDTO(field_name="test", confidence=1.5, evidence_summary="bad")

    def test_next_opportunity_priority_validation(self):
        with pytest.raises(ValidationError):
            NextOpportunityDTO(opportunity="test", reason="test", priority="urgent")


# ── Parser Tests ──────────────────────────────────────────────────────────


class TestParser:
    def test_parse_valid_json(self, parser):
        content = '{"experience_growth": [], "career_fields": [], "strengths": [], "next_opportunities": []}'  # noqa: E501
        result = parser.parse(content)
        assert result.experience_growth == []
        assert result.career_fields == []

    def test_parse_with_fences(self, parser):
        content = '```json\n{"experience_growth": [], "career_fields": [], "strengths": [], "next_opportunities": []}\n```'  # noqa: E501
        result = parser.parse(content)
        assert result.experience_growth == []

    def test_parse_with_prose_prefix(self, parser):
        content = (
            "Here is the analysis:\n\n"
            '{"experience_growth": [], "career_fields": [], "strengths": [], "next_opportunities": []}'  # noqa: E501
        )
        result = parser.parse(content)
        assert result.experience_growth == []

    def test_parse_invalid_json_raises(self, parser):
        with pytest.raises(Exception):
            parser.parse("not json at all")

    def test_parse_empty_raises(self, parser):
        with pytest.raises(Exception):
            parser.parse("")

    def test_parse_partial_object_raises(self, parser):
        with pytest.raises(Exception):
            parser.parse('{"experience_growth": [')  # truncated JSON

    def test_parse_unknown_references_filtered(self, parser):
        content = (
            '{"experience_growth": [{"area": "Test", "description": "desc", '
            '"evidence_resume_version_id": "fake-uuid", '
            '"evidence_analysis_id": "fake-ana-id", '
            '"related_skills": []}], '
            '"career_fields": [], "strengths": [], "next_opportunities": []}'
        )
        result = parser.parse(content)
        assert len(result.experience_growth) == 1  # parser doesn't filter; service does


# ── Service: Deterministic Skill Changes ──────────────────────────────────


class TestServiceDeterministic:
    @pytest.mark.asyncio
    async def test_no_resumes(self):
        resume_repo = AsyncMock()
        resume_repo.list_by_user.return_value = []
        service = CareerInsightService(
            resume_repository=resume_repo,
            resume_analysis_repository=AsyncMock(),
            job_analysis_repository=AsyncMock(),
            tailoring_session_repository=AsyncMock(),
            chat_service=AsyncMock(),
        )
        result = await service.generate_insight(user_id=_make_uuid(99))
        assert result.overview.total_resumes_analyzed == 0
        assert result.data_version_pairs == 0
        assert result.skill_changes.added == []

    @pytest.mark.asyncio
    async def test_one_version_no_analysis(self):
        rid = _make_uuid(1)
        vid = _make_uuid(10)
        resume = _mock_resume(
            resume_id=rid, versions=[_mock_version(version_id=vid, resume_id=rid)]
        )
        resume_repo = AsyncMock()
        resume_repo.list_by_user.return_value = [resume]
        resume_repo.get.return_value = resume
        analysis_repo = AsyncMock()
        analysis_repo.list_by_user.return_value = []
        ja_repo = AsyncMock()
        ja_repo.list_by_user.return_value = []
        tailoring_repo = AsyncMock()
        tailoring_repo.list_by_user.return_value = []

        service = CareerInsightService(
            resume_repository=resume_repo,
            resume_analysis_repository=analysis_repo,
            job_analysis_repository=ja_repo,
            tailoring_session_repository=tailoring_repo,
            chat_service=AsyncMock(),
        )
        result = await service.generate_insight(user_id=_make_uuid(99))
        assert result.overview.total_resumes_analyzed == 1
        assert result.data_version_pairs == 0

    @pytest.mark.asyncio
    async def test_two_versions_with_added_skills(self):
        rid = _make_uuid(1)
        vid1 = _make_uuid(10)
        vid2 = _make_uuid(11)
        v1 = _mock_version(
            version_id=vid1, resume_id=rid, version_number=1, content="I know Python."
        )
        v2 = _mock_version(
            version_id=vid2,
            resume_id=rid,
            version_number=2,
            content="I know Python and Kubernetes.",
        )
        resume = _mock_resume(resume_id=rid, versions=[v1, v2])

        a1 = _mock_analysis(
            analysis_id=_make_uuid(20),
            resume_id=rid,
            version_id=vid1,
            skills=[("Python", "technical")],
            ats_score=70,
        )
        a2 = _mock_analysis(
            analysis_id=_make_uuid(21),
            resume_id=rid,
            version_id=vid2,
            skills=[("Python", "technical"), ("Kubernetes", "technical")],
            ats_score=85,
        )

        resume_repo = AsyncMock()
        resume_repo.list_by_user.return_value = [resume]
        resume_repo.get.return_value = resume
        analysis_repo = AsyncMock()
        analysis_repo.list_by_user.return_value = [a1, a2]
        ja_repo = AsyncMock()
        ja_repo.list_by_user.return_value = []
        tailoring_repo = AsyncMock()
        tailoring_repo.list_by_user.return_value = []

        chat_service = AsyncMock()
        # Needs to return a valid LLM response for the pair to try LLM
        chat_service.chat.return_value = MagicMock(
            content='{"experience_growth": [], "career_fields": [], "strengths": [], "next_opportunities": []}'  # noqa: E501
        )

        service = CareerInsightService(
            resume_repository=resume_repo,
            resume_analysis_repository=analysis_repo,
            job_analysis_repository=ja_repo,
            tailoring_session_repository=tailoring_repo,
            chat_service=chat_service,
        )
        result = await service.generate_insight(user_id=_make_uuid(99))
        assert result.data_version_pairs == 1
        assert len(result.skill_changes.added) == 1
        assert result.skill_changes.added[0].skill_name == "Kubernetes"
        assert result.skill_changes.added[0].previous_skill_count == 0
        assert result.skill_changes.added[0].current_skill_count == 1
        assert result.overview.ats_delta == 15  # 85 - 70

    @pytest.mark.asyncio
    async def test_two_versions_with_removed_skills(self):
        rid = _make_uuid(1)
        vid1 = _make_uuid(10)
        vid2 = _make_uuid(11)
        v1 = _mock_version(
            version_id=vid1, resume_id=rid, version_number=1, content="PHP and Python."
        )
        v2 = _mock_version(
            version_id=vid2, resume_id=rid, version_number=2, content="Python only."
        )
        resume = _mock_resume(resume_id=rid, versions=[v1, v2])

        a1 = _mock_analysis(
            analysis_id=_make_uuid(20),
            resume_id=rid,
            version_id=vid1,
            skills=[("PHP", "technical"), ("Python", "technical")],
        )
        a2 = _mock_analysis(
            analysis_id=_make_uuid(21),
            resume_id=rid,
            version_id=vid2,
            skills=[("Python", "technical")],
        )

        resume_repo = AsyncMock()
        resume_repo.list_by_user.return_value = [resume]
        resume_repo.get.return_value = resume
        analysis_repo = AsyncMock()
        analysis_repo.list_by_user.return_value = [a1, a2]
        ja_repo = AsyncMock()
        ja_repo.list_by_user.return_value = []
        tailoring_repo = AsyncMock()
        tailoring_repo.list_by_user.return_value = []

        chat_service = AsyncMock()
        chat_service.chat.return_value = MagicMock(
            content='{"experience_growth": [], "career_fields": [], "strengths": [], "next_opportunities": []}'  # noqa: E501
        )
        service = CareerInsightService(
            resume_repository=resume_repo,
            resume_analysis_repository=analysis_repo,
            job_analysis_repository=ja_repo,
            tailoring_session_repository=tailoring_repo,
            chat_service=chat_service,
        )
        result = await service.generate_insight(user_id=_make_uuid(99))
        assert len(result.skill_changes.removed) == 1
        assert result.skill_changes.removed[0].skill_name == "PHP"
        assert result.skill_changes.removed[0].previous_skill_count == 1
        assert result.skill_changes.removed[0].current_skill_count == 0

    @pytest.mark.asyncio
    async def test_same_skill_increased_mention_count(self):
        rid = _make_uuid(1)
        vid1 = _make_uuid(10)
        vid2 = _make_uuid(11)
        v1 = _mock_version(
            version_id=vid1, resume_id=rid, version_number=1, content="Python."
        )
        v2 = _mock_version(
            version_id=vid2,
            resume_id=rid,
            version_number=2,
            content="Python Python Python.",
        )
        resume = _mock_resume(resume_id=rid, versions=[v1, v2])

        a1 = _mock_analysis(
            analysis_id=_make_uuid(20),
            resume_id=rid,
            version_id=vid1,
            skills=[("Python", "technical"), ("Python", "technical")],
            ats_score=70,
        )
        a2 = _mock_analysis(
            analysis_id=_make_uuid(21),
            resume_id=rid,
            version_id=vid2,
            skills=[
                ("Python", "technical"),
                ("Python", "technical"),
                ("Python", "technical"),
            ],
            ats_score=85,
        )

        resume_repo = AsyncMock()
        resume_repo.list_by_user.return_value = [resume]
        resume_repo.get.return_value = resume
        analysis_repo = AsyncMock()
        analysis_repo.list_by_user.return_value = [a1, a2]
        ja_repo = AsyncMock()
        ja_repo.list_by_user.return_value = []
        tailoring_repo = AsyncMock()
        tailoring_repo.list_by_user.return_value = []

        chat_service = AsyncMock()
        chat_service.chat.return_value = MagicMock(
            content='{"experience_growth": [], "career_fields": [], "strengths": [], "next_opportunities": []}'  # noqa: E501
        )
        service = CareerInsightService(
            resume_repository=resume_repo,
            resume_analysis_repository=analysis_repo,
            job_analysis_repository=ja_repo,
            tailoring_session_repository=tailoring_repo,
            chat_service=chat_service,
        )
        result = await service.generate_insight(user_id=_make_uuid(99))
        assert len(result.skill_changes.strengthened) == 1
        assert result.skill_changes.strengthened[0].skill_name == "Python"
        assert result.skill_changes.strengthened[0].previous_skill_count == 2
        assert result.skill_changes.strengthened[0].current_skill_count == 3

    @pytest.mark.asyncio
    async def test_missing_analysis_for_one_version(self):
        rid = _make_uuid(1)
        vid1 = _make_uuid(10)
        vid2 = _make_uuid(11)
        v1 = _mock_version(version_id=vid1, resume_id=rid, version_number=1)
        v2 = _mock_version(version_id=vid2, resume_id=rid, version_number=2)
        resume = _mock_resume(resume_id=rid, versions=[v1, v2])

        a2 = _mock_analysis(
            analysis_id=_make_uuid(21),
            resume_id=rid,
            version_id=vid2,
            skills=[("Python", "technical")],
        )

        resume_repo = AsyncMock()
        resume_repo.list_by_user.return_value = [resume]
        resume_repo.get.return_value = resume
        analysis_repo = AsyncMock()
        analysis_repo.list_by_user.return_value = [a2]
        ja_repo = AsyncMock()
        ja_repo.list_by_user.return_value = []
        tailoring_repo = AsyncMock()
        tailoring_repo.list_by_user.return_value = []

        service = CareerInsightService(
            resume_repository=resume_repo,
            resume_analysis_repository=analysis_repo,
            job_analysis_repository=ja_repo,
            tailoring_session_repository=tailoring_repo,
            chat_service=AsyncMock(),
        )
        result = await service.generate_insight(user_id=_make_uuid(99))
        # No pair can be compared since v1 has no analysis
        assert result.data_version_pairs == 0
        assert len(result.skill_changes.added) == 0

    @pytest.mark.asyncio
    async def test_multiple_resumes(self):
        rid1 = _make_uuid(1)
        rid2 = _make_uuid(2)
        vid1 = _make_uuid(10)
        vid2 = _make_uuid(11)
        vid3 = _make_uuid(12)

        v1 = _mock_version(
            version_id=vid1, resume_id=rid1, version_number=1, content="Python."
        )
        v2 = _mock_version(
            version_id=vid2, resume_id=rid1, version_number=2, content="Python and Go."
        )
        v3 = _mock_version(
            version_id=vid3, resume_id=rid2, version_number=1, content="Java."
        )

        resume1 = _mock_resume(resume_id=rid1, versions=[v1, v2])
        resume2 = _mock_resume(resume_id=rid2, versions=[v3])

        a1 = _mock_analysis(
            analysis_id=_make_uuid(20),
            resume_id=rid1,
            version_id=vid1,
            skills=[("Python", "technical")],
        )
        a2 = _mock_analysis(
            analysis_id=_make_uuid(21),
            resume_id=rid1,
            version_id=vid2,
            skills=[("Python", "technical"), ("Go", "technical")],
        )
        a3 = _mock_analysis(
            analysis_id=_make_uuid(22),
            resume_id=rid2,
            version_id=vid3,
            skills=[("Java", "technical")],
        )

        resume_repo = AsyncMock()
        resume_repo.list_by_user.return_value = [resume1, resume2]
        resume_repo.get.side_effect = [resume1, resume2]
        analysis_repo = AsyncMock()
        analysis_repo.list_by_user.return_value = [a1, a2, a3]
        ja_repo = AsyncMock()
        ja_repo.list_by_user.return_value = []
        tailoring_repo = AsyncMock()
        tailoring_repo.list_by_user.return_value = []

        chat_service = AsyncMock()
        chat_service.chat.return_value = MagicMock(
            content='{"experience_growth": [], "career_fields": [], "strengths": [], "next_opportunities": []}'  # noqa: E501
        )
        service = CareerInsightService(
            resume_repository=resume_repo,
            resume_analysis_repository=analysis_repo,
            job_analysis_repository=ja_repo,
            tailoring_session_repository=tailoring_repo,
            chat_service=chat_service,
        )
        result = await service.generate_insight(user_id=_make_uuid(99))
        assert result.overview.total_resumes_analyzed == 2
        assert result.data_version_pairs == 1  # only resume1 has a pair
        assert len(result.skill_changes.added) == 1
        assert result.skill_changes.added[0].skill_name == "Go"


# ── Service: LLM Integration ──────────────────────────────────────────────


class TestServiceLLMIntegration:
    @pytest.mark.asyncio
    async def test_llm_returns_valid_insights(self):
        rid = _make_uuid(1)
        vid1 = _make_uuid(10)
        vid2 = _make_uuid(11)
        v1 = _mock_version(
            version_id=vid1, resume_id=rid, version_number=1, content="Python."
        )
        v2 = _mock_version(
            version_id=vid2, resume_id=rid, version_number=2, content="Python and Go."
        )
        resume = _mock_resume(resume_id=rid, versions=[v1, v2])

        a1 = _mock_analysis(
            analysis_id=_make_uuid(20),
            resume_id=rid,
            version_id=vid1,
            skills=[("Python", "technical")],
            ats_score=70,
        )
        a2 = _mock_analysis(
            analysis_id=_make_uuid(21),
            resume_id=rid,
            version_id=vid2,
            skills=[("Python", "technical"), ("Go", "technical")],
            ats_score=85,
        )

        resume_repo = AsyncMock()
        resume_repo.list_by_user.return_value = [resume]
        resume_repo.get.return_value = resume
        analysis_repo = AsyncMock()
        analysis_repo.list_by_user.return_value = [a1, a2]
        ja_repo = AsyncMock()
        ja_repo.list_by_user.return_value = []
        tailoring_repo = AsyncMock()
        tailoring_repo.list_by_user.return_value = []

        chat_service = AsyncMock()
        chat_service.chat.return_value = MagicMock(
            content=(
                '{"experience_growth": [{"area": "Backend Engineering", '  # noqa: E501
                '"description": "Added Go skills", '
                '"evidence_resume_version_id": "' + str(vid2) + '", '
                '"evidence_analysis_id": "' + str(a2.id) + '", '
                '"source_snippet": "Python and Go", "related_skills": ["Go"]}], '
                '"career_fields": [{"field_name": "Backend", "confidence": 0.8, '  # noqa: E501
                '"evidence_summary": "Strong backend skills", '
                '"matching_skills": ["Python", "Go"], "job_analysis_ids": [], '
                '"tailoring_session_ids": [], "resume_version_ids": ["'
                + str(vid2)
                + '"]}], '
                '"strengths": [{"title": "Backend", "description": "Good", '  # noqa: E501
                '"evidence_analysis_ids": ["' + str(a2.id) + '"], '
                '"evidence_job_analysis_ids": [], "source_snippets": ["Python and Go"]}], '  # noqa: E501
                '"next_opportunities": [{"opportunity": "Learn K8s", '  # noqa: E501
                '"reason": "Growing field", "priority": "high", '
                '"evidence_job_analysis_ids": [], "evidence_missing_skills": [], '  # noqa: E501
                '"related_field": "Backend"}]}'
            )
        )

        service = CareerInsightService(
            resume_repository=resume_repo,
            resume_analysis_repository=analysis_repo,
            job_analysis_repository=ja_repo,
            tailoring_session_repository=tailoring_repo,
            chat_service=chat_service,
        )
        result = await service.generate_insight(user_id=_make_uuid(99))
        assert len(result.experience_growth) == 1
        assert result.experience_growth[0].area == "Backend Engineering"
        assert len(result.career_fields) == 1
        assert result.career_fields[0].field_name == "Backend"
        assert len(result.strengths) == 1
        assert len(result.next_opportunities) == 1

    @pytest.mark.asyncio
    async def test_llm_invalid_json_returns_deterministic_only(self):
        rid = _make_uuid(1)
        vid1 = _make_uuid(10)
        vid2 = _make_uuid(11)
        v1 = _mock_version(
            version_id=vid1, resume_id=rid, version_number=1, content="Python."
        )
        v2 = _mock_version(
            version_id=vid2, resume_id=rid, version_number=2, content="Python and Go."
        )
        resume = _mock_resume(resume_id=rid, versions=[v1, v2])

        a1 = _mock_analysis(
            analysis_id=_make_uuid(20),
            resume_id=rid,
            version_id=vid1,
            skills=[("Python", "technical")],
            ats_score=70,
        )
        a2 = _mock_analysis(
            analysis_id=_make_uuid(21),
            resume_id=rid,
            version_id=vid2,
            skills=[("Python", "technical"), ("Go", "technical")],
            ats_score=85,
        )

        resume_repo = AsyncMock()
        resume_repo.list_by_user.return_value = [resume]
        resume_repo.get.return_value = resume
        analysis_repo = AsyncMock()
        analysis_repo.list_by_user.return_value = [a1, a2]
        ja_repo = AsyncMock()
        ja_repo.list_by_user.return_value = []
        tailoring_repo = AsyncMock()
        tailoring_repo.list_by_user.return_value = []

        chat_service = AsyncMock()
        chat_service.chat.return_value = MagicMock(content="not valid json at all")

        service = CareerInsightService(
            resume_repository=resume_repo,
            resume_analysis_repository=analysis_repo,
            job_analysis_repository=ja_repo,
            tailoring_session_repository=tailoring_repo,
            chat_service=chat_service,
        )
        result = await service.generate_insight(user_id=_make_uuid(99))
        # Should still return deterministic skill changes
        assert result.overview.ats_delta == 15
        assert len(result.skill_changes.added) == 1
        # But no AI-generated fields
        assert result.experience_growth == []

    @pytest.mark.asyncio
    async def test_llm_unknown_ids_filtered(self):
        rid = _make_uuid(1)
        vid1 = _make_uuid(10)
        vid2 = _make_uuid(11)
        v1 = _mock_version(
            version_id=vid1, resume_id=rid, version_number=1, content="Python."
        )
        v2 = _mock_version(
            version_id=vid2, resume_id=rid, version_number=2, content="Python and Go."
        )
        resume = _mock_resume(resume_id=rid, versions=[v1, v2])

        a1 = _mock_analysis(
            analysis_id=_make_uuid(20),
            resume_id=rid,
            version_id=vid1,
            skills=[("Python", "technical")],
        )
        a2 = _mock_analysis(
            analysis_id=_make_uuid(21),
            resume_id=rid,
            version_id=vid2,
            skills=[("Python", "technical"), ("Go", "technical")],
        )

        resume_repo = AsyncMock()
        resume_repo.list_by_user.return_value = [resume]
        resume_repo.get.return_value = resume
        analysis_repo = AsyncMock()
        analysis_repo.list_by_user.return_value = [a1, a2]
        ja_repo = AsyncMock()
        ja_repo.list_by_user.return_value = []
        tailoring_repo = AsyncMock()
        tailoring_repo.list_by_user.return_value = []

        chat_service = AsyncMock()
        chat_service.chat.return_value = MagicMock(
            content=(
                '{"experience_growth": [{"area": "Fake", "description": "Fake", '
                '"evidence_resume_version_id": "unknown-version-id", '
                '"evidence_analysis_id": "unknown-analysis-id", '
                '"related_skills": []}], '
                '"career_fields": [], "strengths": [], "next_opportunities": []}'
            )
        )

        service = CareerInsightService(
            resume_repository=resume_repo,
            resume_analysis_repository=analysis_repo,
            job_analysis_repository=ja_repo,
            tailoring_session_repository=tailoring_repo,
            chat_service=chat_service,
        )
        result = await service.generate_insight(user_id=_make_uuid(99))
        # The experience_growth referencing unknown IDs should be filtered out
        assert result.experience_growth == []


# ── Utility Tests ─────────────────────────────────────────────────────────


class TestUtilities:
    def test_find_skill_snippet_found(self):
        content = "I have experience with Python and Django."
        snippet = _find_skill_snippet("Python", content)
        assert snippet is not None
        assert "Python" in snippet

    def test_find_skill_snippet_not_found(self):
        snippet = _find_skill_snippet("Kubernetes", "Python only")
        assert snippet is None

    def test_find_skill_snippet_empty_content(self):
        snippet = _find_skill_snippet("Python", "")
        assert snippet is None

    def test_find_skill_snippet_case_insensitive(self):
        content = "I use python every day."
        snippet = _find_skill_snippet("Python", content)
        assert snippet is not None

    def test_format_skill_changes_empty(self):
        result = _format_skill_changes(SkillChangesDTO())
        assert result == "No skill changes detected."

    def test_format_skill_changes_with_added(self):
        changes = SkillChangesDTO(
            added=[
                SkillChangeDTO(
                    skill_name="Go", category="technical", current_skill_count=1
                )
            ]
        )
        result = _format_skill_changes(changes)
        assert "Added Skills" in result
        assert "Go" in result


# ── CareerInsightResponse Merge Test ──────────────────────────────────────


class TestResponseMerge:
    def test_successful_structured_merge(self):
        """Verify that deterministic + AI fields merge into a valid response."""
        resp = CareerInsightResponse(
            overview=CareerOverviewDTO(
                latest_ats_score=85,
                previous_ats_score=70,
                ats_delta=15,
                total_resumes_analyzed=1,
                total_versions_compared=2,
            ),
            skill_changes=SkillChangesDTO(
                added=[
                    SkillChangeDTO(
                        skill_name="Go", category="technical", current_skill_count=1
                    )
                ]
            ),
            experience_growth=[
                ExperienceGrowthDTO(
                    area="Backend", description="Added Go", related_skills=["Go"]
                )
            ],
            career_fields=[
                CareerFieldDTO(
                    field_name="Backend", confidence=0.8, evidence_summary="Good"
                )
            ],
            strengths=[
                StrengthDTO(
                    title="Backend", description="Strong", source_snippets=["Go"]
                )
            ],
            next_opportunities=[
                NextOpportunityDTO(
                    opportunity="Learn K8s", reason="Trending", priority="high"
                )
            ],
            data_version_pairs=1,
        )
        assert resp.overview.ats_delta == 15
        assert len(resp.skill_changes.added) == 1
        assert len(resp.experience_growth) == 1
        assert len(resp.career_fields) == 1
        assert len(resp.strengths) == 1
        assert len(resp.next_opportunities) == 1
        assert resp.data_version_pairs == 1
