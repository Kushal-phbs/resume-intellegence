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
    service = DashboardService(
        dashboard_repository,
        analytics_repository,
        activity_repository,
    )
    return service, dashboard_repository, analytics_repository, activity_repository


def test_get_statistics_aggregates_totals_and_success_rate() -> None:
    service, dashboards, analytics, activities = _build_service()
    user_id = uuid4()
    now = datetime.now(UTC)
    dashboards.latest_snapshot.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_resumes=3,
        total_resume_analyses=2,
        total_job_analyses=4,
        total_tailoring_sessions=1,
        average_resume_score=80,
        average_job_match_score=70,
        average_tailoring_score=90,
        generated_cover_letters=2,
        created_at=now,
        updated_at=now,
    )
    analytics.get_by_user.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_ai_requests=10,
        total_tokens_used=5000,
        successful_requests=8,
        failed_requests=2,
        average_processing_time_ms=250,
        last_activity_at=now,
        created_at=now,
        updated_at=now,
    )
    activities.list_recent_activity.return_value = []

    stats = asyncio.run(service.get_statistics(user_id=user_id))

    assert stats["total_analyses"] == 6
    assert stats["success_rate"] == 80.0
    assert stats["total_exports"] == 2


def test_get_trends_returns_chart_points_in_chronological_order() -> None:
    service, dashboards, _analytics, _activities = _build_service()
    user_id = uuid4()
    older = datetime(2026, 7, 1, tzinfo=UTC)
    newer = datetime(2026, 7, 2, tzinfo=UTC)
    dashboards.get_by_user.return_value = [
        SimpleNamespace(
            created_at=newer,
            total_resumes=2,
            total_resume_analyses=2,
            total_job_analyses=2,
            total_tailoring_sessions=1,
            generated_cover_letters=1,
            average_resume_score=82,
            average_job_match_score=78,
            average_tailoring_score=88,
        ),
        SimpleNamespace(
            created_at=older,
            total_resumes=1,
            total_resume_analyses=1,
            total_job_analyses=1,
            total_tailoring_sessions=1,
            generated_cover_letters=1,
            average_resume_score=80,
            average_job_match_score=76,
            average_tailoring_score=86,
        ),
    ]

    points = asyncio.run(service.get_trends(user_id=user_id, points=5))

    assert points[0]["timestamp"] == older
    assert points[1]["timestamp"] == newer


def test_get_performance_defaults_when_missing_analytics() -> None:
    service, _dashboards, analytics, _activities = _build_service()
    user_id = uuid4()
    analytics.get_by_user.return_value = None

    performance = asyncio.run(service.get_performance(user_id=user_id))

    assert performance["user_id"] == user_id
    assert performance["total_ai_requests"] == 0
    assert performance["success_rate"] == 0.0
