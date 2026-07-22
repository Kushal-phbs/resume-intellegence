from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.job_analysis import router as job_analysis_router
from app.core.exceptions import ResourceNotFoundException
from app.core.handlers import register_exception_handlers
from app.dependencies.auth import get_current_user
from app.dependencies.job_analysis import get_job_analysis_service
from app.enums import JobAnalysisStatus
from app.schemas.job_analysis import (
    JobAnalysisResponse,
    JobAnalysisSummaryResponse,
    KeywordMatchResponse,
    MatchedSkillResponse,
    MissingSkillResponse,
)


class _JobAnalysisServiceStub:
    def __init__(self, owner_id: UUID) -> None:
        self.owner_id = owner_id
        self.calls: list[tuple[str, object, object | None]] = []
        self.analysis_response = _analysis_response(owner_id)
        self.summary_response = _summary_response(owner_id)
        self.matched_skills_response = _matched_skills_response(
            self.analysis_response.id
        )
        self.missing_skills_response = _missing_skills_response(
            self.analysis_response.id
        )
        self.keywords_response = _keywords_response(self.analysis_response.id)
        self.history_response = [self.summary_response]
        self.missing_analysis = False
        self.missing_resume = False
        self.missing_job = False

    async def analyze_job_match(
        self,
        *,
        user_id: UUID,
        resume_id: UUID,
        job_description_id: UUID,
    ) -> JobAnalysisResponse:
        self.calls.append(("analyze_job_match", user_id, resume_id))
        self._assert_owner(user_id)
        if self.missing_resume:
            raise ResourceNotFoundException("Resume not found")
        if self.missing_job:
            raise ResourceNotFoundException("Job description not found")
        return self.analysis_response

    async def get_analysis(
        self, *, user_id: UUID, analysis_id: UUID
    ) -> JobAnalysisResponse:
        self.calls.append(("get_analysis", user_id, analysis_id))
        self._assert_owner(user_id)
        if self.missing_analysis:
            raise ResourceNotFoundException("Job analysis not found")
        return self.analysis_response

    async def get_summary(
        self, *, user_id: UUID, analysis_id: UUID
    ) -> JobAnalysisSummaryResponse:
        self.calls.append(("get_summary", user_id, analysis_id))
        self._assert_owner(user_id)
        if self.missing_analysis:
            raise ResourceNotFoundException("Job analysis not found")
        return self.summary_response

    async def get_matched_skills(
        self, *, user_id: UUID, analysis_id: UUID
    ) -> list[MatchedSkillResponse]:
        self.calls.append(("get_matched_skills", user_id, analysis_id))
        self._assert_owner(user_id)
        if self.missing_analysis:
            raise ResourceNotFoundException("Job analysis not found")
        return self.matched_skills_response

    async def get_missing_skills(
        self, *, user_id: UUID, analysis_id: UUID
    ) -> list[MissingSkillResponse]:
        self.calls.append(("get_missing_skills", user_id, analysis_id))
        self._assert_owner(user_id)
        if self.missing_analysis:
            raise ResourceNotFoundException("Job analysis not found")
        return self.missing_skills_response

    async def get_keyword_matches(
        self, *, user_id: UUID, analysis_id: UUID
    ) -> list[KeywordMatchResponse]:
        self.calls.append(("get_keyword_matches", user_id, analysis_id))
        self._assert_owner(user_id)
        if self.missing_analysis:
            raise ResourceNotFoundException("Job analysis not found")
        return self.keywords_response

    async def list_history(self, *, user_id: UUID) -> list[JobAnalysisSummaryResponse]:
        self.calls.append(("list_history", user_id, None))
        self._assert_owner(user_id)
        return self.history_response

    async def delete_analysis(self, *, user_id: UUID, analysis_id: UUID) -> None:
        self.calls.append(("delete_analysis", user_id, analysis_id))
        self._assert_owner(user_id)
        if self.missing_analysis:
            raise ResourceNotFoundException("Job analysis not found")

    def _assert_owner(self, user_id: UUID) -> None:
        if user_id != self.owner_id:
            raise ResourceNotFoundException("Job analysis not found")


def _analysis_response(owner_id: UUID) -> JobAnalysisResponse:
    now = datetime.now(UTC)
    analysis_id = uuid4()
    return JobAnalysisResponse(
        id=analysis_id,
        resume_id=uuid4(),
        job_description_id=uuid4(),
        analysis_status=JobAnalysisStatus.COMPLETED,
        match_score=84,
        ats_match_score=80,
        summary="Strong match with minor cloud gaps.",
        strengths=["Strong backend ownership"],
        weaknesses=["Limited cloud infra depth"],
        recommendations=["Add deployment impact metrics"],
        matched_skills=_matched_skills_response(analysis_id),
        missing_skills=_missing_skills_response(analysis_id),
        keyword_matches=_keywords_response(analysis_id),
        created_at=now,
        updated_at=now,
        error_message=None,
    )


def _summary_response(owner_id: UUID) -> JobAnalysisSummaryResponse:
    now = datetime.now(UTC)
    return JobAnalysisSummaryResponse(
        id=uuid4(),
        resume_id=uuid4(),
        job_description_id=uuid4(),
        analysis_status=JobAnalysisStatus.COMPLETED,
        match_score=84,
        ats_match_score=80,
        strengths=["Strong backend ownership"],
        weaknesses=["Limited cloud infra depth"],
        recommendations=["Add deployment impact metrics"],
        created_at=now,
        updated_at=now,
        error_message=None,
    )


def _matched_skills_response(analysis_id: UUID) -> list[MatchedSkillResponse]:
    now = datetime.now(UTC)
    return [
        MatchedSkillResponse(
            id=uuid4(),
            job_analysis_id=analysis_id,
            skill_name="Python",
            created_at=now,
            updated_at=now,
        )
    ]


def _missing_skills_response(analysis_id: UUID) -> list[MissingSkillResponse]:
    now = datetime.now(UTC)
    return [
        MissingSkillResponse(
            id=uuid4(),
            job_analysis_id=analysis_id,
            skill_name="Kubernetes",
            created_at=now,
            updated_at=now,
        )
    ]


def _keywords_response(analysis_id: UUID) -> list[KeywordMatchResponse]:
    now = datetime.now(UTC)
    return [
        KeywordMatchResponse(
            id=uuid4(),
            job_analysis_id=analysis_id,
            keyword="FastAPI",
            created_at=now,
            updated_at=now,
        )
    ]


def _build_app(service_stub: _JobAnalysisServiceStub, current_user_id: UUID) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(job_analysis_router)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=current_user_id
    )
    app.dependency_overrides[get_job_analysis_service] = lambda: service_stub
    return app


def _make_client(
    service_stub: _JobAnalysisServiceStub, current_user_id: UUID
) -> TestClient:
    return TestClient(_build_app(service_stub, current_user_id))


def test_post_job_analysis_success() -> None:
    user_id = uuid4()
    service_stub = _JobAnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.post(f"/job-analysis/{uuid4()}/{uuid4()}")

    assert response.status_code == 201
    assert response.json()["analysis_status"] == JobAnalysisStatus.COMPLETED.value


def test_post_job_analysis_missing_resume() -> None:
    user_id = uuid4()
    service_stub = _JobAnalysisServiceStub(owner_id=user_id)
    service_stub.missing_resume = True
    client = _make_client(service_stub, user_id)

    response = client.post(f"/job-analysis/{uuid4()}/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"


def test_get_job_analysis_success() -> None:
    user_id = uuid4()
    analysis_id = uuid4()
    service_stub = _JobAnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get(f"/job-analysis/{analysis_id}")

    assert response.status_code == 200
    assert response.json()["summary"] == "Strong match with minor cloud gaps."


def test_get_job_analysis_summary_success() -> None:
    user_id = uuid4()
    analysis_id = uuid4()
    service_stub = _JobAnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get(f"/job-analysis/{analysis_id}/summary")

    assert response.status_code == 200
    assert response.json()["match_score"] == 84
    assert "matched_skills" not in response.json()


def test_get_job_analysis_matched_skills_success() -> None:
    user_id = uuid4()
    analysis_id = uuid4()
    service_stub = _JobAnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get(f"/job-analysis/{analysis_id}/matched-skills")

    assert response.status_code == 200
    assert response.json()[0]["skill_name"] == "Python"


def test_get_job_analysis_missing_skills_success() -> None:
    user_id = uuid4()
    analysis_id = uuid4()
    service_stub = _JobAnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get(f"/job-analysis/{analysis_id}/missing-skills")

    assert response.status_code == 200
    assert response.json()[0]["skill_name"] == "Kubernetes"


def test_get_job_analysis_keywords_success() -> None:
    user_id = uuid4()
    analysis_id = uuid4()
    service_stub = _JobAnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get(f"/job-analysis/{analysis_id}/keywords")

    assert response.status_code == 200
    assert response.json()[0]["keyword"] == "FastAPI"


def test_get_job_analysis_history_success() -> None:
    user_id = uuid4()
    service_stub = _JobAnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get("/job-analysis/history")

    assert response.status_code == 200
    assert response.json()[0]["ats_match_score"] == 80


def test_delete_job_analysis_success() -> None:
    user_id = uuid4()
    analysis_id = uuid4()
    service_stub = _JobAnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.delete(f"/job-analysis/{analysis_id}")

    assert response.status_code == 204


def test_job_analysis_ownership_validation() -> None:
    owner_id = uuid4()
    other_user_id = uuid4()
    analysis_id = uuid4()
    service_stub = _JobAnalysisServiceStub(owner_id=owner_id)
    client = _make_client(service_stub, other_user_id)

    response = client.get(f"/job-analysis/{analysis_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job analysis not found"


def test_openapi_exposes_job_analysis_paths() -> None:
    user_id = uuid4()
    service_stub = _JobAnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    openapi = client.get("/openapi.json").json()

    assert "/job-analysis/{resume_id}/{job_id}" in openapi["paths"]
    assert "/job-analysis/history" in openapi["paths"]
    security_schemes = openapi["components"]["securitySchemes"]
    assert any(
        scheme.get("type") == "http" and scheme.get("scheme") == "bearer"
        for scheme in security_schemes.values()
    )
