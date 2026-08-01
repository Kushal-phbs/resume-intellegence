from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from app.services.dashboard_service import DashboardService


def _user(user_id):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=user_id,
        email="user@example.com",
        full_name="User",
        role="user",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def test_dashboard_overview_uses_notification_repository_for_unread_notifications() -> (
    None
):
    user_id = uuid4()
    dashboards = AsyncMock()
    analytics = AsyncMock()
    activities = AsyncMock()
    resumes = AsyncMock()
    resume_analyses = AsyncMock()
    job_analyses = AsyncMock()
    notifications = AsyncMock()
    users = AsyncMock()

    users.get_by_id.return_value = _user(user_id)
    resumes.list_by_user.return_value = []
    resume_analyses.list_by_user.return_value = []
    job_analyses.list_by_user.return_value = []
    analytics.get_by_user.return_value = None

    now = datetime.now(UTC)
    notifications.list_unread.return_value = [
        SimpleNamespace(
            id=uuid4(),
            type="resume_uploaded",
            message="Resume uploaded",
            metadata_json={"entity_id": str(uuid4())},
            created_at=now,
        )
    ]

    activities.list_recent_activity.side_effect = AssertionError(
        "notifications must not be sourced from activity repository"
    )

    service = DashboardService(
        dashboards,
        analytics,
        activities,
        resumes,
        resume_analyses,
        job_analyses,
        notifications,
        users,
    )

    result = asyncio.run(service.get_dashboard_overview(user_id=user_id))

    assert len(result.unread_notifications) == 1
    notifications.list_unread.assert_awaited_once_with(user_id, limit=100)
