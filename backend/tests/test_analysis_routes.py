from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.analysis import router as analysis_router
from app.core.exceptions import ResumeNotFoundException, ValidationException
from app.core.handlers import register_exception_handlers
from app.dependencies.analysis import get_analysis_service
from app.dependencies.auth import get_current_user
from app.enums import AnalysisStatus, SkillCategory
from app.schemas.analysis import (
    KeywordResponse,
    ResumeAnalysisResponse,
    ResumeAnalysisSummaryResponse,
    SkillResponse,
)


class _AnalysisServiceStub:
    def __init__(self, owner_id: UUID) -> None:
        self.owner_id = owner_id
        self.calls: list[tuple[str, object, object]] = []
        self.analysis_response = _analysis_response(owner_id=owner_id)
        self.summary_response = _summary_response(owner_id=owner_id)
        self.skills_response = _skills_response()
        self.keywords_response = _keywords_response()
        self.history_response = [self.summary_response]
        self.raise_duplicate = False
        self.missing_analysis = False
        self.missing_resume = False
        self.unauthorized = False

    async def analyze_resume(
        self, user_id: UUID, resume_id: UUID
    ) -> ResumeAnalysisResponse:
        self.calls.append(("analyze_resume", user_id, resume_id))
        self._assert_owner(user_id)
        if self.unauthorized:
            raise ResumeNotFoundException("Analysis not found")
        if self.raise_duplicate:
            raise ValidationException(
                "An analysis is already in progress for this resume",
                status_code=409,
            )
        if self.missing_resume:
            raise ResumeNotFoundException()
        return self.analysis_response

    async def get_latest_analysis(
        self, user_id: UUID, resume_id: UUID
    ) -> ResumeAnalysisResponse:
        self.calls.append(("get_latest_analysis", user_id, resume_id))
        self._assert_owner(user_id)
        if self.missing_analysis:
            raise ResumeNotFoundException("Analysis not found")
        return self.analysis_response

    async def get_latest_summary(
        self, user_id: UUID, resume_id: UUID
    ) -> ResumeAnalysisSummaryResponse:
        self.calls.append(("get_latest_summary", user_id, resume_id))
        self._assert_owner(user_id)
        if self.missing_analysis:
            raise ResumeNotFoundException("Analysis not found")
        return self.summary_response

    async def get_latest_skills(
        self, user_id: UUID, resume_id: UUID
    ) -> list[SkillResponse]:
        self.calls.append(("get_latest_skills", user_id, resume_id))
        self._assert_owner(user_id)
        if self.missing_analysis:
            raise ResumeNotFoundException("Analysis not found")
        return self.skills_response

    async def get_latest_keywords(
        self, user_id: UUID, resume_id: UUID
    ) -> list[KeywordResponse]:
        self.calls.append(("get_latest_keywords", user_id, resume_id))
        self._assert_owner(user_id)
        if self.missing_analysis:
            raise ResumeNotFoundException("Analysis not found")
        return self.keywords_response

    async def list_analyses(
        self, user_id: UUID, resume_id: UUID
    ) -> list[ResumeAnalysisSummaryResponse]:
        self.calls.append(("list_analyses", user_id, resume_id))
        self._assert_owner(user_id)
        return self.history_response

    async def delete_analysis(self, user_id: UUID, analysis_id: UUID) -> None:
        self.calls.append(("delete_analysis", user_id, analysis_id))
        self._assert_owner(user_id)
        if self.missing_analysis:
            raise ResumeNotFoundException("Analysis not found")

    def _assert_owner(self, user_id: UUID) -> None:
        if self.unauthorized or user_id != self.owner_id:
            raise ResumeNotFoundException("Analysis not found")


def _analysis_response(owner_id: UUID) -> ResumeAnalysisResponse:
    now = datetime.now(UTC)
    analysis_id = uuid4()
    skill_id = uuid4()
    keyword_id = uuid4()
    return ResumeAnalysisResponse(
        id=analysis_id,
        resume_id=owner_id,
        resume_version_id=uuid4(),
        analysis_status=AnalysisStatus.COMPLETED,
        resume_score=91,
        ats_score=88,
        strengths=["Clear structure"],
        weaknesses=["Could quantify more"],
        recommendations=["Add metrics"],
        skills=[
            SkillResponse(
                id=skill_id,
                analysis_id=analysis_id,
                skill_name="Python",
                category=SkillCategory.TECHNICAL,
                created_at=now,
                updated_at=now,
            )
        ],
        keywords=[
            KeywordResponse(
                id=keyword_id,
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


def _summary_response(owner_id: UUID) -> ResumeAnalysisSummaryResponse:
    now = datetime.now(UTC)
    return ResumeAnalysisSummaryResponse(
        id=uuid4(),
        resume_id=owner_id,
        resume_version_id=uuid4(),
        analysis_status=AnalysisStatus.COMPLETED,
        resume_score=91,
        ats_score=88,
        strengths=["Clear structure"],
        weaknesses=["Could quantify more"],
        recommendations=["Add metrics"],
        skill_count=1,
        keyword_count=1,
        created_at=now,
        updated_at=now,
        error_message=None,
    )


def _skills_response() -> list[SkillResponse]:
    now = datetime.now(UTC)
    analysis_id = uuid4()
    return [
        SkillResponse(
            id=uuid4(),
            analysis_id=analysis_id,
            skill_name="Python",
            category=SkillCategory.TECHNICAL,
            created_at=now,
            updated_at=now,
        )
    ]


def _keywords_response() -> list[KeywordResponse]:
    now = datetime.now(UTC)
    analysis_id = uuid4()
    return [
        KeywordResponse(
            id=uuid4(),
            analysis_id=analysis_id,
            keyword="FastAPI",
            created_at=now,
            updated_at=now,
        )
    ]


def _build_app(service_stub: _AnalysisServiceStub, current_user_id: UUID) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(analysis_router)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=current_user_id
    )
    app.dependency_overrides[get_analysis_service] = lambda: service_stub
    return app


def _make_client(
    service_stub: _AnalysisServiceStub, current_user_id: UUID
) -> TestClient:
    return TestClient(_build_app(service_stub, current_user_id))


def test_post_analysis_success() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _AnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.post(f"/analysis/{resume_id}")

    assert response.status_code == 201
    assert response.json()["analysis_status"] == AnalysisStatus.COMPLETED.value
    assert service_stub.calls[0][0] == "analyze_resume"


def test_post_analysis_resume_not_found() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _AnalysisServiceStub(owner_id=user_id)
    service_stub.missing_resume = True
    client = _make_client(service_stub, user_id)

    response = client.post(f"/analysis/{resume_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"


def test_post_analysis_unauthorized() -> None:
    user_id = uuid4()
    other_user_id = uuid4()
    resume_id = uuid4()
    service_stub = _AnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, other_user_id)

    response = client.post(f"/analysis/{resume_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Analysis not found"


def test_post_analysis_duplicate_active() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _AnalysisServiceStub(owner_id=user_id)
    service_stub.raise_duplicate = True
    client = _make_client(service_stub, user_id)

    response = client.post(f"/analysis/{resume_id}")

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "An analysis is already in progress for this resume"
    )


def test_get_analysis_success() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _AnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get(f"/analysis/{resume_id}")

    assert response.status_code == 200
    assert response.json()["resume_id"] == str(user_id)
    assert response.json()["skills"][0]["skill_name"] == "Python"


def test_get_analysis_not_found() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _AnalysisServiceStub(owner_id=user_id)
    service_stub.missing_analysis = True
    client = _make_client(service_stub, user_id)

    response = client.get(f"/analysis/{resume_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Analysis not found"


def test_get_analysis_ownership_validation() -> None:
    user_id = uuid4()
    other_user_id = uuid4()
    resume_id = uuid4()
    service_stub = _AnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, other_user_id)

    response = client.get(f"/analysis/{resume_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Analysis not found"


def test_get_analysis_summary_success() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _AnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get(f"/analysis/{resume_id}/summary")

    assert response.status_code == 200
    assert response.json()["ats_score"] == 88
    assert "skills" not in response.json()


def test_get_analysis_skills_success() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _AnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get(f"/analysis/{resume_id}/skills")

    assert response.status_code == 200
    assert response.json()[0]["skill_name"] == "Python"


def test_get_analysis_keywords_success() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _AnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get(f"/analysis/{resume_id}/keywords")

    assert response.status_code == 200
    assert response.json()[0]["keyword"] == "FastAPI"


def test_get_analysis_history_success() -> None:
    user_id = uuid4()
    resume_id = uuid4()
    service_stub = _AnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get(f"/analysis/{resume_id}/history")

    assert response.status_code == 200
    assert response.json()[0]["skill_count"] == 1


def test_delete_analysis_success() -> None:
    user_id = uuid4()
    analysis_id = uuid4()
    service_stub = _AnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.delete(f"/analysis/{analysis_id}")

    assert response.status_code == 204
    assert service_stub.calls[0][0] == "delete_analysis"


def test_openapi_exposes_bearer_security_and_response_schemas() -> None:
    user_id = uuid4()
    service_stub = _AnalysisServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    openapi = client.get("/openapi.json").json()

    security_schemes = openapi["components"]["securitySchemes"]
    assert any(
        scheme.get("type") == "http" and scheme.get("scheme") == "bearer"
        for scheme in security_schemes.values()
    )
    summary_schema = openapi["paths"]["/analysis/{resume_id}/summary"]["get"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"]
    assert "$ref" in summary_schema
