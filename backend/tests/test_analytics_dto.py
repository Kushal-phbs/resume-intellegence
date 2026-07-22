from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.dto.analytics import (
    ActivityDTO,
    AnalyticsDTO,
    DashboardDTO,
    DashboardSummaryDTO,
)
from app.enums.analytics import ActivityType, EntityType


def test_dashboard_dto_accepts_valid_payload() -> None:
    dto = DashboardDTO(
        user_id=uuid4(),
        total_resumes=2,
        total_resume_analyses=3,
        total_job_analyses=1,
        total_tailoring_sessions=1,
        average_resume_score=85.5,
        average_job_match_score=88.2,
        average_tailoring_score=90.1,
        generated_cover_letters=1,
    )

    assert dto.total_resumes == 2
    assert dto.average_tailoring_score == 90.1


def test_dashboard_dto_rejects_negative_counts() -> None:
    with pytest.raises(ValueError):
        DashboardDTO(
            user_id=uuid4(),
            total_resumes=-1,
            total_resume_analyses=0,
            total_job_analyses=0,
            total_tailoring_sessions=0,
            average_resume_score=50,
            average_job_match_score=50,
            average_tailoring_score=50,
            generated_cover_letters=0,
        )


def test_analytics_dto_rejects_failed_requests_exceeding_total() -> None:
    with pytest.raises(ValueError):
        AnalyticsDTO(
            user_id=uuid4(),
            total_ai_requests=1,
            total_tokens_used=100,
            successful_requests=0,
            failed_requests=2,
            average_processing_time_ms=200,
            last_activity_at=datetime.now(UTC),
        )


def test_analytics_dto_rejects_successful_requests_exceeding_total() -> None:
    with pytest.raises(ValueError):
        AnalyticsDTO(
            user_id=uuid4(),
            total_ai_requests=2,
            total_tokens_used=100,
            successful_requests=3,
            failed_requests=0,
            average_processing_time_ms=200,
            last_activity_at=datetime.now(UTC),
        )


def test_activity_dto_accepts_enum_values() -> None:
    dto = ActivityDTO(
        user_id=uuid4(),
        activity_type=ActivityType.LOGIN,
        entity_type=EntityType.EXPORT,
        entity_id=None,
        metadata_json={"ip": "127.0.0.1"},
    )

    assert dto.activity_type == ActivityType.LOGIN
    assert dto.entity_type == EntityType.EXPORT


def test_activity_dto_defaults_empty_metadata() -> None:
    dto = ActivityDTO(
        user_id=uuid4(),
        activity_type=ActivityType.RESUME_UPLOADED,
        entity_type=EntityType.RESUME,
        entity_id=uuid4(),
    )

    assert dto.metadata_json == {}


def test_dashboard_summary_dto_composes_nested_payloads() -> None:
    user_id = uuid4()
    snapshot = DashboardDTO(
        user_id=user_id,
        total_resumes=2,
        total_resume_analyses=1,
        total_job_analyses=1,
        total_tailoring_sessions=1,
        average_resume_score=80,
        average_job_match_score=70,
        average_tailoring_score=90,
        generated_cover_letters=1,
    )
    analytics = AnalyticsDTO(
        user_id=user_id,
        total_ai_requests=4,
        total_tokens_used=1200,
        successful_requests=3,
        failed_requests=1,
        average_processing_time_ms=300,
        last_activity_at=datetime.now(UTC),
    )
    activity = ActivityDTO(
        user_id=user_id,
        activity_type=ActivityType.RESUME_ANALYZED,
        entity_type=EntityType.ANALYSIS,
        entity_id=uuid4(),
        metadata_json={"source": "test"},
    )

    summary = DashboardSummaryDTO(
        snapshot=snapshot,
        analytics=analytics,
        recent_activity=[activity],
    )

    assert summary.analytics.total_ai_requests == 4
    assert summary.recent_activity[0].activity_type == ActivityType.RESUME_ANALYZED


def test_dashboard_summary_dto_defaults_recent_activity_list() -> None:
    user_id = uuid4()
    summary = DashboardSummaryDTO(
        snapshot=DashboardDTO(
            user_id=user_id,
            total_resumes=0,
            total_resume_analyses=0,
            total_job_analyses=0,
            total_tailoring_sessions=0,
            average_resume_score=None,
            average_job_match_score=None,
            average_tailoring_score=None,
            generated_cover_letters=0,
        ),
        analytics=AnalyticsDTO(
            user_id=user_id,
            total_ai_requests=0,
            total_tokens_used=0,
            successful_requests=0,
            failed_requests=0,
            average_processing_time_ms=None,
            last_activity_at=None,
        ),
    )

    assert summary.recent_activity == []
