from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.enums.analytics import ActivityType, EntityType
from app.models.activity_log import ActivityLog
from app.models.dashboard_snapshot import DashboardSnapshot
from app.models.user_analytics import UserAnalytics
from app.repositories.activity_repository import ActivityRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.dashboard_repository import DashboardRepository


def _build_session_mock() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


def _scalar_result(value: object) -> MagicMock:
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


def test_dashboard_repository_create() -> None:
    session = _build_session_mock()
    repository = DashboardRepository(session)

    row = asyncio.run(
        repository.create(
            user_id=uuid4(),
            total_resumes=1,
            total_resume_analyses=2,
            total_job_analyses=3,
            total_tailoring_sessions=4,
            average_resume_score=80,
            average_job_match_score=81,
            average_tailoring_score=82,
            generated_cover_letters=2,
        )
    )

    assert isinstance(row, DashboardSnapshot)
    assert row.total_job_analyses == 3
    session.add.assert_called_once_with(row)


def test_dashboard_repository_update() -> None:
    session = _build_session_mock()
    repository = DashboardRepository(session)
    row = SimpleNamespace(id=uuid4(), total_resumes=1)
    repository.get_by_id = AsyncMock(side_effect=[row, row])

    updated = asyncio.run(repository.update(row.id, total_resumes=5))

    assert updated is row
    assert row.total_resumes == 5


def test_dashboard_repository_delete() -> None:
    session = _build_session_mock()
    repository = DashboardRepository(session)
    row = SimpleNamespace(id=uuid4())
    repository.get_by_id = AsyncMock(return_value=row)

    deleted = asyncio.run(repository.delete(row.id))

    assert deleted is True
    session.delete.assert_awaited_once_with(row)


def test_dashboard_repository_get_by_user_returns_rows() -> None:
    session = _build_session_mock()
    repository = DashboardRepository(session)
    expected = [SimpleNamespace(id=uuid4())]
    result = MagicMock()
    result.scalars.return_value.all.return_value = expected
    session.execute = AsyncMock(return_value=result)

    rows = asyncio.run(repository.get_by_user(uuid4()))

    assert rows == expected


def test_dashboard_repository_latest_snapshot() -> None:
    session = _build_session_mock()
    repository = DashboardRepository(session)
    expected = SimpleNamespace(id=uuid4())
    result = MagicMock()
    result.scalar_one_or_none.return_value = expected
    session.execute = AsyncMock(return_value=result)

    row = asyncio.run(repository.latest_snapshot(uuid4()))

    assert row is expected


def test_dashboard_repository_calculate_metrics_aggregates_scalars() -> None:
    session = _build_session_mock()
    repository = DashboardRepository(session)
    session.execute = AsyncMock(
        side_effect=[
            _scalar_result(2),
            _scalar_result(3),
            _scalar_result(4),
            _scalar_result(5),
            _scalar_result(6),
            _scalar_result(88.5),
            _scalar_result(77.25),
            _scalar_result(91.0),
        ]
    )

    metrics = asyncio.run(repository.calculate_metrics(uuid4()))

    assert metrics["total_resumes"] == 2
    assert metrics["total_job_analyses"] == 4
    assert metrics["generated_cover_letters"] == 6
    assert metrics["average_resume_score"] == 88.5


def test_analytics_repository_create() -> None:
    session = _build_session_mock()
    repository = AnalyticsRepository(session)

    row = asyncio.run(
        repository.create(
            user_id=uuid4(),
            total_ai_requests=1,
            total_tokens_used=2,
            successful_requests=1,
            failed_requests=0,
            average_processing_time_ms=100,
            last_activity_at=datetime.now(UTC),
        )
    )

    assert isinstance(row, UserAnalytics)
    assert row.total_ai_requests == 1


def test_analytics_repository_update() -> None:
    session = _build_session_mock()
    repository = AnalyticsRepository(session)
    row = SimpleNamespace(id=uuid4(), total_tokens_used=10)
    repository.get_by_id = AsyncMock(side_effect=[row, row])

    updated = asyncio.run(repository.update(row.id, total_tokens_used=25))

    assert updated is row
    assert row.total_tokens_used == 25


def test_analytics_repository_delete_returns_false_for_missing_row() -> None:
    session = _build_session_mock()
    repository = AnalyticsRepository(session)
    repository.get_by_id = AsyncMock(return_value=None)

    deleted = asyncio.run(repository.delete(uuid4()))

    assert deleted is False


def test_analytics_repository_get_by_user() -> None:
    session = _build_session_mock()
    repository = AnalyticsRepository(session)
    expected = SimpleNamespace(id=uuid4())
    result = MagicMock()
    result.scalar_one_or_none.return_value = expected
    session.execute = AsyncMock(return_value=result)

    row = asyncio.run(repository.get_by_user(uuid4()))

    assert row is expected


def test_activity_repository_create() -> None:
    session = _build_session_mock()
    repository = ActivityRepository(session)

    row = asyncio.run(
        repository.create(
            user_id=uuid4(),
            activity_type=ActivityType.LOGIN,
            entity_type=EntityType.EXPORT,
            entity_id=None,
            metadata_json={"ip": "127.0.0.1"},
        )
    )

    assert isinstance(row, ActivityLog)
    assert row.activity_type == ActivityType.LOGIN.value


def test_activity_repository_record_activity_alias() -> None:
    session = _build_session_mock()
    repository = ActivityRepository(session)
    repository.create = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

    row = asyncio.run(
        repository.record_activity(
            user_id=uuid4(),
            activity_type=ActivityType.RESUME_UPLOADED,
            entity_type=EntityType.RESUME,
            entity_id=uuid4(),
            metadata_json={"filename": "resume.pdf"},
        )
    )

    assert row.id is not None
    repository.create.assert_awaited_once()


def test_activity_repository_update() -> None:
    session = _build_session_mock()
    repository = ActivityRepository(session)
    row = SimpleNamespace(id=uuid4(), metadata_json={})
    repository.get_by_id = AsyncMock(side_effect=[row, row])

    updated = asyncio.run(repository.update(row.id, metadata_json={"a": 1}))

    assert updated is row
    assert row.metadata_json == {"a": 1}


def test_activity_repository_get_by_user() -> None:
    session = _build_session_mock()
    repository = ActivityRepository(session)
    expected = [SimpleNamespace(id=uuid4())]
    result = MagicMock()
    result.scalars.return_value.all.return_value = expected
    session.execute = AsyncMock(return_value=result)

    rows = asyncio.run(repository.get_by_user(uuid4()))

    assert rows == expected


def test_activity_repository_list_recent_activity() -> None:
    session = _build_session_mock()
    repository = ActivityRepository(session)
    expected = [SimpleNamespace(id=uuid4())]
    result = MagicMock()
    result.scalars.return_value.all.return_value = expected
    session.execute = AsyncMock(return_value=result)

    rows = asyncio.run(repository.list_recent_activity(uuid4(), limit=5))

    assert rows == expected


def test_activity_repository_delete() -> None:
    session = _build_session_mock()
    repository = ActivityRepository(session)
    row = SimpleNamespace(id=uuid4())
    repository.get_by_id = AsyncMock(return_value=row)

    deleted = asyncio.run(repository.delete(row.id))

    assert deleted is True
    session.delete.assert_awaited_once_with(row)
