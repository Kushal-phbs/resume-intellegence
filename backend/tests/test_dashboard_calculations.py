from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from app.services.dashboard_service import DashboardService


def _build_service() -> tuple[DashboardService, AsyncMock, AsyncMock, AsyncMock]:
    dashboard_repository = AsyncMock()
    analytics_repository = AsyncMock()
    activity_repository = AsyncMock()
    return (
        DashboardService(
            dashboard_repository,
            analytics_repository,
            activity_repository,
        ),
        dashboard_repository,
        analytics_repository,
        activity_repository,
    )


def test_calculate_dashboard_metrics_handles_none_averages() -> None:
    service, dashboards, _analytics, _activities = _build_service()
    dashboards.calculate_metrics.return_value = {
        "total_resumes": 1,
        "total_resume_analyses": 0,
        "total_job_analyses": 0,
        "total_tailoring_sessions": 0,
        "average_resume_score": None,
        "average_job_match_score": None,
        "average_tailoring_score": None,
        "generated_cover_letters": 0,
    }

    dto = asyncio.run(service.calculate_dashboard_metrics(user_id=uuid4()))

    assert dto.average_resume_score is None
    assert dto.average_job_match_score is None
    assert dto.average_tailoring_score is None


def test_calculate_dashboard_metrics_casts_counts_to_int() -> None:
    service, dashboards, _analytics, _activities = _build_service()
    dashboards.calculate_metrics.return_value = {
        "total_resumes": 2.0,
        "total_resume_analyses": 3.0,
        "total_job_analyses": 4.0,
        "total_tailoring_sessions": 5.0,
        "average_resume_score": 60.0,
        "average_job_match_score": 70.0,
        "average_tailoring_score": 80.0,
        "generated_cover_letters": 1.0,
    }

    dto = asyncio.run(service.calculate_dashboard_metrics(user_id=uuid4()))

    assert isinstance(dto.total_resumes, int)
    assert dto.total_resumes == 2
    assert isinstance(dto.generated_cover_letters, int)


def test_update_analytics_weighted_average_formula() -> None:
    service, _dashboards, analytics, _activities = _build_service()
    user_id = uuid4()
    now = datetime.now(UTC)
    analytics.get_by_user.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_ai_requests=4,
        total_tokens_used=100,
        successful_requests=4,
        failed_requests=0,
        average_processing_time_ms=250.0,
        last_activity_at=now,
        created_at=now,
        updated_at=now,
    )
    analytics.update.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_ai_requests=5,
        total_tokens_used=120,
        successful_requests=5,
        failed_requests=0,
        average_processing_time_ms=300.0,
        last_activity_at=now,
        created_at=now,
        updated_at=now,
    )

    dto = asyncio.run(
        service.update_analytics(
            user_id=user_id,
            tokens_used=20,
            processing_time_ms=500,
            successful=True,
            activity_at=now,
        )
    )

    assert dto.average_processing_time_ms == 300.0


def test_get_dashboard_summary_initializes_default_analytics() -> None:
    service, dashboards, analytics, activities = _build_service()
    user_id = uuid4()
    now = datetime.now(UTC)
    dashboards.latest_snapshot.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_resumes=0,
        total_resume_analyses=0,
        total_job_analyses=0,
        total_tailoring_sessions=0,
        average_resume_score=None,
        average_job_match_score=None,
        average_tailoring_score=None,
        generated_cover_letters=0,
        created_at=now,
        updated_at=now,
    )
    analytics.get_by_user.return_value = None
    activities.list_recent_activity.return_value = []

    summary = asyncio.run(service.get_dashboard_summary(user_id=user_id))

    assert summary.analytics.total_ai_requests == 0
    assert summary.analytics.last_activity_at is None
