from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from app.enums.analytics import ActivityType, EntityType
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


def test_calculate_dashboard_metrics_rounds_averages() -> None:
    service, dashboards, _analytics, _activities = _build_service()
    user_id = uuid4()
    dashboards.calculate_metrics.return_value = {
        "total_resumes": 2,
        "total_resume_analyses": 3,
        "total_job_analyses": 4,
        "total_tailoring_sessions": 5,
        "average_resume_score": 88.126,
        "average_job_match_score": 79.994,
        "average_tailoring_score": None,
        "generated_cover_letters": 6,
    }

    dto = asyncio.run(service.calculate_dashboard_metrics(user_id=user_id))

    assert dto.average_resume_score == 88.13
    assert dto.average_job_match_score == 79.99
    assert dto.average_tailoring_score is None


def test_generate_dashboard_snapshot_persists_metrics() -> None:
    service, dashboards, _analytics, _activities = _build_service()
    user_id = uuid4()
    now = datetime.now(UTC)
    dashboards.calculate_metrics.return_value = {
        "total_resumes": 1,
        "total_resume_analyses": 1,
        "total_job_analyses": 1,
        "total_tailoring_sessions": 1,
        "average_resume_score": 70,
        "average_job_match_score": 75,
        "average_tailoring_score": 80,
        "generated_cover_letters": 1,
    }
    dashboards.create.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_resumes=1,
        total_resume_analyses=1,
        total_job_analyses=1,
        total_tailoring_sessions=1,
        average_resume_score=70,
        average_job_match_score=75,
        average_tailoring_score=80,
        generated_cover_letters=1,
        created_at=now,
        updated_at=now,
    )

    dto = asyncio.run(service.generate_dashboard_snapshot(user_id=user_id))

    assert dto.id is not None
    dashboards.create.assert_awaited_once()


def test_update_analytics_creates_record_when_missing() -> None:
    service, _dashboards, analytics, _activities = _build_service()
    user_id = uuid4()
    now = datetime.now(UTC)
    analytics.get_by_user.return_value = None
    analytics.create.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_ai_requests=1,
        total_tokens_used=500,
        successful_requests=1,
        failed_requests=0,
        average_processing_time_ms=210,
        last_activity_at=now,
        created_at=now,
        updated_at=now,
    )

    dto = asyncio.run(
        service.update_analytics(
            user_id=user_id,
            tokens_used=500,
            processing_time_ms=210,
            successful=True,
            activity_at=now,
        )
    )

    assert dto.total_ai_requests == 1
    assert dto.successful_requests == 1


def test_update_analytics_updates_existing_average() -> None:
    service, _dashboards, analytics, _activities = _build_service()
    user_id = uuid4()
    now = datetime.now(UTC)
    current = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_ai_requests=2,
        total_tokens_used=1000,
        successful_requests=2,
        failed_requests=0,
        average_processing_time_ms=200.0,
        last_activity_at=now,
        created_at=now,
        updated_at=now,
    )
    analytics.get_by_user.return_value = current
    analytics.update.return_value = SimpleNamespace(
        id=current.id,
        user_id=user_id,
        total_ai_requests=3,
        total_tokens_used=1300,
        successful_requests=2,
        failed_requests=1,
        average_processing_time_ms=300.0,
        last_activity_at=now,
        created_at=now,
        updated_at=now,
    )

    dto = asyncio.run(
        service.update_analytics(
            user_id=user_id,
            tokens_used=300,
            processing_time_ms=500,
            successful=False,
            activity_at=now,
        )
    )

    assert dto.total_ai_requests == 3
    assert dto.failed_requests == 1
    assert dto.average_processing_time_ms == 300.0


def test_update_analytics_clamps_negative_inputs() -> None:
    service, _dashboards, analytics, _activities = _build_service()
    user_id = uuid4()
    now = datetime.now(UTC)
    analytics.get_by_user.return_value = None
    analytics.create.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_ai_requests=1,
        total_tokens_used=0,
        successful_requests=0,
        failed_requests=1,
        average_processing_time_ms=0.0,
        last_activity_at=now,
        created_at=now,
        updated_at=now,
    )

    dto = asyncio.run(
        service.update_analytics(
            user_id=user_id,
            tokens_used=-50,
            processing_time_ms=-1,
            successful=False,
            activity_at=now,
        )
    )

    assert dto.total_tokens_used == 0
    assert dto.average_processing_time_ms == 0.0


def test_record_activity_returns_dto() -> None:
    service, _dashboards, _analytics, activities = _build_service()
    user_id = uuid4()
    now = datetime.now(UTC)
    activities.record_activity.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        activity_type=ActivityType.LOGIN.value,
        entity_type=EntityType.EXPORT.value,
        entity_id=None,
        metadata_json={"ip": "127.0.0.1"},
        created_at=now,
    )

    dto = asyncio.run(
        service.record_activity(
            user_id=user_id,
            activity_type=ActivityType.LOGIN,
            entity_type=EntityType.EXPORT,
            entity_id=None,
            metadata_json={"ip": "127.0.0.1"},
        )
    )

    assert dto.activity_type == ActivityType.LOGIN
    assert dto.metadata_json["ip"] == "127.0.0.1"


def test_get_dashboard_summary_uses_latest_snapshot_when_present() -> None:
    service, dashboards, analytics, activities = _build_service()
    user_id = uuid4()
    now = datetime.now(UTC)
    dashboards.latest_snapshot.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_resumes=2,
        total_resume_analyses=2,
        total_job_analyses=2,
        total_tailoring_sessions=1,
        average_resume_score=80,
        average_job_match_score=78,
        average_tailoring_score=88,
        generated_cover_letters=1,
        created_at=now,
        updated_at=now,
    )
    analytics.get_by_user.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_ai_requests=4,
        total_tokens_used=2000,
        successful_requests=3,
        failed_requests=1,
        average_processing_time_ms=250,
        last_activity_at=now,
        created_at=now,
        updated_at=now,
    )
    activities.list_recent_activity.return_value = []

    summary = asyncio.run(service.get_dashboard_summary(user_id=user_id))

    assert summary.snapshot.total_resumes == 2
    assert summary.analytics.total_ai_requests == 4


def test_get_dashboard_summary_generates_snapshot_when_missing() -> None:
    service, dashboards, analytics, activities = _build_service()
    user_id = uuid4()
    now = datetime.now(UTC)
    dashboards.latest_snapshot.return_value = None
    dashboards.calculate_metrics.return_value = {
        "total_resumes": 0,
        "total_resume_analyses": 0,
        "total_job_analyses": 0,
        "total_tailoring_sessions": 0,
        "average_resume_score": None,
        "average_job_match_score": None,
        "average_tailoring_score": None,
        "generated_cover_letters": 0,
    }
    dashboards.create.return_value = SimpleNamespace(
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

    assert summary.snapshot.total_resumes == 0
    dashboards.create.assert_awaited_once()


def test_get_dashboard_summary_uses_activity_limit() -> None:
    service, dashboards, analytics, activities = _build_service()
    user_id = uuid4()
    now = datetime.now(UTC)
    dashboards.latest_snapshot.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_resumes=1,
        total_resume_analyses=1,
        total_job_analyses=1,
        total_tailoring_sessions=1,
        average_resume_score=90,
        average_job_match_score=90,
        average_tailoring_score=90,
        generated_cover_letters=1,
        created_at=now,
        updated_at=now,
    )
    analytics.get_by_user.return_value = None
    activities.list_recent_activity.return_value = []

    _summary = asyncio.run(
        service.get_dashboard_summary(user_id=user_id, activity_limit=5)
    )

    activities.list_recent_activity.assert_awaited_once_with(user_id, limit=5)


def test_get_dashboard_summary_maps_recent_activity() -> None:
    service, dashboards, analytics, activities = _build_service()
    user_id = uuid4()
    now = datetime.now(UTC)
    dashboards.latest_snapshot.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_resumes=1,
        total_resume_analyses=1,
        total_job_analyses=1,
        total_tailoring_sessions=1,
        average_resume_score=90,
        average_job_match_score=90,
        average_tailoring_score=90,
        generated_cover_letters=1,
        created_at=now,
        updated_at=now,
    )
    analytics.get_by_user.return_value = None
    activities.list_recent_activity.return_value = [
        SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            activity_type=ActivityType.EXPORT_GENERATED.value,
            entity_type=EntityType.EXPORT.value,
            entity_id=uuid4(),
            metadata_json={"format": "pdf"},
            created_at=now,
        )
    ]

    summary = asyncio.run(service.get_dashboard_summary(user_id=user_id))

    assert summary.recent_activity[0].activity_type == ActivityType.EXPORT_GENERATED
    assert summary.recent_activity[0].metadata_json["format"] == "pdf"
