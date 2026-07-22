from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.dashboard import router as dashboard_router
from app.core.handlers import register_exception_handlers
from app.dependencies.auth import get_current_user
from app.dependencies.dashboard import get_dashboard_service


class _AggregationServiceStub:
    async def get_statistics(self, *, user_id):
        _ = user_id
        return {
            "total_resumes": 4,
            "total_analyses": 7,
            "total_tailoring_sessions": 3,
            "total_exports": 2,
            "average_ats_score": 82.5,
            "average_job_match_score": 76.0,
            "average_tailoring_score": 88.0,
            "total_ai_requests": 15,
            "success_rate": 86.67,
            "average_processing_time_ms": 210.0,
            "total_tokens_used": 7200,
        }

    async def get_trends(self, *, user_id, points=12):
        _ = (user_id, points)
        return [
            {
                "timestamp": datetime.now(UTC),
                "total_resumes": 4,
                "total_resume_analyses": 3,
                "total_job_analyses": 4,
                "total_tailoring_sessions": 3,
                "generated_cover_letters": 2,
                "average_resume_score": 82.5,
                "average_job_match_score": 76.0,
                "average_tailoring_score": 88.0,
            }
        ]

    async def get_performance(self, *, user_id):
        _ = user_id
        now = datetime.now(UTC)
        return {
            "id": uuid4(),
            "user_id": uuid4(),
            "total_ai_requests": 15,
            "total_tokens_used": 7200,
            "successful_requests": 13,
            "failed_requests": 2,
            "success_rate": 86.67,
            "average_processing_time_ms": 210.0,
            "last_activity_at": now,
            "created_at": now,
            "updated_at": now,
        }

    async def get_dashboard_summary(self, *, user_id, activity_limit=20):
        _ = (user_id, activity_limit)
        now = datetime.now(UTC)
        return SimpleNamespace(
            snapshot=SimpleNamespace(
                total_resumes=4,
                total_resume_analyses=3,
                total_job_analyses=4,
                total_tailoring_sessions=3,
                generated_cover_letters=2,
                average_resume_score=82.5,
                average_job_match_score=76.0,
                average_tailoring_score=88.0,
            ),
            analytics=SimpleNamespace(
                id=uuid4(),
                user_id=uuid4(),
                total_ai_requests=15,
                total_tokens_used=7200,
                successful_requests=13,
                failed_requests=2,
                average_processing_time_ms=210.0,
                last_activity_at=now,
                created_at=now,
                updated_at=now,
            ),
            recent_activity=[],
        )

    async def get_snapshot(self, *, user_id):
        _ = user_id
        return SimpleNamespace(
            total_resumes=4,
            total_resume_analyses=3,
            total_job_analyses=4,
            total_tailoring_sessions=3,
            generated_cover_letters=2,
            average_resume_score=82.5,
            average_job_match_score=76.0,
            average_tailoring_score=88.0,
        )

    async def get_recent_activity(self, *, user_id, limit=20):
        _ = (user_id, limit)
        return []

    async def generate_dashboard_snapshot(self, *, user_id):
        _ = user_id
        return SimpleNamespace(total_resumes=4)


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(dashboard_router)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4())
    app.dependency_overrides[get_dashboard_service] = lambda: _AggregationServiceStub()
    return app


def test_dashboard_statistics_endpoint_returns_aggregated_payload() -> None:
    response = TestClient(_build_app()).get("/dashboard/statistics")

    assert response.status_code == 200
    assert response.json()["total_analyses"] == 7
    assert response.json()["success_rate"] == 86.67


def test_dashboard_performance_endpoint_returns_processing_metrics() -> None:
    response = TestClient(_build_app()).get("/dashboard/performance")

    assert response.status_code == 200
    assert response.json()["average_processing_time_ms"] == 210.0
    assert response.json()["total_tokens_used"] == 7200
