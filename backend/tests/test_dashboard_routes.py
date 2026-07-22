from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.dashboard import router as dashboard_router
from app.core.exceptions import ResourceNotFoundException
from app.core.handlers import register_exception_handlers
from app.dependencies.auth import get_current_user
from app.dependencies.dashboard import get_dashboard_service
from app.dto.analytics import (
    ActivityDTO,
    AnalyticsDTO,
    DashboardDTO,
    DashboardSummaryDTO,
)
from app.enums.analytics import ActivityType, EntityType


class _DashboardServiceStub:
    def __init__(self, owner_id: UUID) -> None:
        self.owner_id = owner_id
        self.refresh_called = False
        now = datetime.now(UTC)
        self.summary = DashboardSummaryDTO(
            snapshot=DashboardDTO(
                id=uuid4(),
                user_id=owner_id,
                total_resumes=3,
                total_resume_analyses=2,
                total_job_analyses=4,
                total_tailoring_sessions=1,
                average_resume_score=81.2,
                average_job_match_score=77.5,
                average_tailoring_score=88.0,
                generated_cover_letters=2,
                created_at=now,
                updated_at=now,
            ),
            analytics=AnalyticsDTO(
                id=uuid4(),
                user_id=owner_id,
                total_ai_requests=10,
                total_tokens_used=3000,
                successful_requests=8,
                failed_requests=2,
                average_processing_time_ms=245.5,
                last_activity_at=now,
                created_at=now,
                updated_at=now,
            ),
            recent_activity=[
                ActivityDTO(
                    id=uuid4(),
                    user_id=owner_id,
                    activity_type=ActivityType.LOGIN,
                    entity_type=EntityType.EXPORT,
                    entity_id=None,
                    metadata_json={"ip": "127.0.0.1"},
                    created_at=now,
                )
            ],
        )

    def _assert_owner(self, user_id: UUID) -> None:
        if user_id != self.owner_id:
            raise ResourceNotFoundException("Dashboard data not found")

    async def get_dashboard_summary(
        self,
        *,
        user_id: UUID,
        activity_limit: int = 20,
    ) -> DashboardSummaryDTO:
        self._assert_owner(user_id)
        _ = activity_limit
        return self.summary

    async def get_snapshot(self, *, user_id: UUID) -> DashboardDTO:
        self._assert_owner(user_id)
        return self.summary.snapshot

    async def get_recent_activity(
        self,
        *,
        user_id: UUID,
        limit: int = 20,
    ) -> list[ActivityDTO]:
        self._assert_owner(user_id)
        _ = limit
        return self.summary.recent_activity

    async def get_statistics(self, *, user_id: UUID) -> dict[str, float | int | None]:
        self._assert_owner(user_id)
        return {
            "total_resumes": 3,
            "total_analyses": 6,
            "total_tailoring_sessions": 1,
            "total_exports": 2,
            "average_ats_score": 81.2,
            "average_job_match_score": 77.5,
            "average_tailoring_score": 88.0,
            "total_ai_requests": 10,
            "success_rate": 80.0,
            "average_processing_time_ms": 245.5,
            "total_tokens_used": 3000,
        }

    async def get_trends(
        self,
        *,
        user_id: UUID,
        points: int = 12,
    ) -> list[dict[str, float | int | datetime | None]]:
        self._assert_owner(user_id)
        _ = points
        return [
            {
                "timestamp": datetime.now(UTC),
                "total_resumes": 3,
                "total_resume_analyses": 2,
                "total_job_analyses": 4,
                "total_tailoring_sessions": 1,
                "generated_cover_letters": 2,
                "average_resume_score": 81.2,
                "average_job_match_score": 77.5,
                "average_tailoring_score": 88.0,
            }
        ]

    async def get_performance(
        self,
        *,
        user_id: UUID,
    ) -> dict[str, float | int | UUID | datetime | None]:
        self._assert_owner(user_id)
        analytics = self.summary.analytics
        return {
            "id": analytics.id,
            "user_id": analytics.user_id,
            "total_ai_requests": analytics.total_ai_requests,
            "total_tokens_used": analytics.total_tokens_used,
            "successful_requests": analytics.successful_requests,
            "failed_requests": analytics.failed_requests,
            "success_rate": 80.0,
            "average_processing_time_ms": analytics.average_processing_time_ms,
            "last_activity_at": analytics.last_activity_at,
            "created_at": analytics.created_at,
            "updated_at": analytics.updated_at,
        }

    async def generate_dashboard_snapshot(self, *, user_id: UUID) -> DashboardDTO:
        self._assert_owner(user_id)
        self.refresh_called = True
        return self.summary.snapshot


def _build_app(service_stub: _DashboardServiceStub, current_user_id: UUID) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(dashboard_router)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=current_user_id
    )
    app.dependency_overrides[get_dashboard_service] = lambda: service_stub
    return app


def _make_client(
    service_stub: _DashboardServiceStub,
    current_user_id: UUID,
) -> TestClient:
    return TestClient(_build_app(service_stub, current_user_id))


def test_get_dashboard_success() -> None:
    user_id = uuid4()
    service_stub = _DashboardServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get("/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total_resumes"] == 3
    assert payload["analytics"]["success_rate"] == 80.0
    assert payload["recent_activity"][0]["activity_type"] == ActivityType.LOGIN.value


def test_get_dashboard_summary_success() -> None:
    user_id = uuid4()
    service_stub = _DashboardServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    assert response.json()["total_job_analyses"] == 4


def test_get_dashboard_activity_success() -> None:
    user_id = uuid4()
    service_stub = _DashboardServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get("/dashboard/activity?limit=10")

    assert response.status_code == 200
    assert response.json()[0]["entity_type"] == EntityType.EXPORT.value


def test_get_dashboard_statistics_success() -> None:
    user_id = uuid4()
    service_stub = _DashboardServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get("/dashboard/statistics")

    assert response.status_code == 200
    assert response.json()["total_analyses"] == 6


def test_get_dashboard_trends_success() -> None:
    user_id = uuid4()
    service_stub = _DashboardServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get("/dashboard/trends?points=8")

    assert response.status_code == 200
    assert len(response.json()["points"]) == 1
    assert response.json()["points"][0]["total_tailoring_sessions"] == 1


def test_get_dashboard_performance_success() -> None:
    user_id = uuid4()
    service_stub = _DashboardServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.get("/dashboard/performance")

    assert response.status_code == 200
    assert response.json()["total_ai_requests"] == 10


def test_post_dashboard_refresh_success() -> None:
    user_id = uuid4()
    service_stub = _DashboardServiceStub(owner_id=user_id)
    client = _make_client(service_stub, user_id)

    response = client.post("/dashboard/refresh")

    assert response.status_code == 201
    assert service_stub.refresh_called is True
    assert response.json()["summary"]["total_resume_analyses"] == 2


def test_dashboard_ownership_validation() -> None:
    owner_id = uuid4()
    other_user_id = uuid4()
    service_stub = _DashboardServiceStub(owner_id=owner_id)
    client = _make_client(service_stub, other_user_id)

    response = client.get("/dashboard")

    assert response.status_code == 404
    assert response.json()["detail"] == "Dashboard data not found"
