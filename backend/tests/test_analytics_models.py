from __future__ import annotations

from sqlalchemy.orm import configure_mappers

from app.models.activity_log import ActivityLog
from app.models.dashboard_snapshot import DashboardSnapshot
from app.models.user import User
from app.models.user_analytics import UserAnalytics


def test_analytics_models_register_expected_tables() -> None:
    assert DashboardSnapshot.__table__.name == "dashboard_snapshots"
    assert UserAnalytics.__table__.name == "user_analytics"
    assert ActivityLog.__table__.name == "activity_logs"


def test_analytics_models_define_check_constraints() -> None:
    dashboard_constraints = {
        constraint.name for constraint in DashboardSnapshot.__table_args__
    }
    user_analytics_constraints = {
        constraint.name for constraint in UserAnalytics.__table_args__
    }
    activity_constraints = {
        constraint.name for constraint in ActivityLog.__table_args__
    }

    assert "ck_dashboard_snapshots_avg_resume_score_range" in dashboard_constraints
    assert "ck_user_analytics_request_counts_valid" in user_analytics_constraints
    assert "ck_activity_logs_activity_type_valid" in activity_constraints


def test_user_relationships_include_analytics_domain() -> None:
    configure_mappers()
    relationships = {rel.key for rel in User.__mapper__.relationships}

    assert "dashboard_snapshots" in relationships
    assert "user_analytics" in relationships
    assert "activity_logs" in relationships
