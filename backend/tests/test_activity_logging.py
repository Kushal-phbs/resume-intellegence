from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from app.enums.analytics import ActivityType, EntityType
from app.repositories.activity_repository import ActivityRepository
from app.services.dashboard_service import DashboardService


def test_dashboard_service_record_activity_maps_enums() -> None:
    dashboards = AsyncMock()
    analytics = AsyncMock()
    activities = AsyncMock()
    service = DashboardService(dashboards, analytics, activities)
    user_id = uuid4()
    now = datetime.now(UTC)
    entity_id = uuid4()
    activities.record_activity.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        activity_type=ActivityType.RESUME_TAILORED.value,
        entity_type=EntityType.TAILORING.value,
        entity_id=entity_id,
        metadata_json={"source": "service"},
        created_at=now,
    )

    dto = asyncio.run(
        service.record_activity(
            user_id=user_id,
            activity_type=ActivityType.RESUME_TAILORED,
            entity_type=EntityType.TAILORING,
            entity_id=entity_id,
            metadata_json={"source": "service"},
        )
    )

    assert dto.activity_type == ActivityType.RESUME_TAILORED
    assert dto.entity_type == EntityType.TAILORING


def test_dashboard_service_summary_returns_recent_activity_items() -> None:
    dashboards = AsyncMock()
    analytics = AsyncMock()
    activities = AsyncMock()
    service = DashboardService(dashboards, analytics, activities)
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
        average_job_match_score=85,
        average_tailoring_score=88,
        generated_cover_letters=1,
        created_at=now,
        updated_at=now,
    )
    analytics.get_by_user.return_value = None
    activities.list_recent_activity.return_value = [
        SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            activity_type=ActivityType.LOGIN.value,
            entity_type=EntityType.EXPORT.value,
            entity_id=None,
            metadata_json={"ip": "127.0.0.1"},
            created_at=now,
        )
    ]

    summary = asyncio.run(service.get_dashboard_summary(user_id=user_id))

    assert len(summary.recent_activity) == 1
    assert summary.recent_activity[0].activity_type == ActivityType.LOGIN


def test_activity_repository_record_activity_passes_through_to_create() -> None:
    repository = ActivityRepository(AsyncMock())
    repository.create = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

    _result = asyncio.run(
        repository.record_activity(
            user_id=uuid4(),
            activity_type=ActivityType.EXPORT_GENERATED,
            entity_type=EntityType.EXPORT,
            entity_id=uuid4(),
            metadata_json={"format": "pdf"},
        )
    )

    repository.create.assert_awaited_once()


def test_activity_repository_update_missing_returns_none() -> None:
    repository = ActivityRepository(AsyncMock())
    repository.get_by_id = AsyncMock(return_value=None)

    result = asyncio.run(repository.update(uuid4(), metadata_json={"x": 1}))

    assert result is None
