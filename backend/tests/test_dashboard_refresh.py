from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from app.services.dashboard_service import DashboardService


def test_generate_dashboard_snapshot_uses_calculated_metrics() -> None:
    dashboards = AsyncMock()
    analytics = AsyncMock()
    activities = AsyncMock()
    service = DashboardService(dashboards, analytics, activities)
    user_id = uuid4()
    now = datetime.now(UTC)
    dashboards.calculate_metrics.return_value = {
        "total_resumes": 5,
        "total_resume_analyses": 4,
        "total_job_analyses": 3,
        "total_tailoring_sessions": 2,
        "average_resume_score": 80.0,
        "average_job_match_score": 75.0,
        "average_tailoring_score": 90.0,
        "generated_cover_letters": 1,
    }
    dashboards.create.return_value = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        total_resumes=5,
        total_resume_analyses=4,
        total_job_analyses=3,
        total_tailoring_sessions=2,
        average_resume_score=80.0,
        average_job_match_score=75.0,
        average_tailoring_score=90.0,
        generated_cover_letters=1,
        created_at=now,
        updated_at=now,
    )

    snapshot = asyncio.run(service.generate_dashboard_snapshot(user_id=user_id))

    assert snapshot.total_resumes == 5
    dashboards.create.assert_awaited_once()
