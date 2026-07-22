from __future__ import annotations

from pathlib import Path

_MIGRATION_NAME = (
    "alembic/versions/20260722_1210_c7a9f1b2d3e4_add_analytics_domain_tables.py"
)


def test_analytics_migration_contains_expected_tables() -> None:
    migration_path = Path(__file__).resolve().parents[1] / _MIGRATION_NAME
    content = migration_path.read_text(encoding="utf-8")

    assert '"dashboard_snapshots"' in content
    assert '"user_analytics"' in content
    assert '"activity_logs"' in content


def test_analytics_migration_contains_check_constraints() -> None:
    migration_path = Path(__file__).resolve().parents[1] / _MIGRATION_NAME
    content = migration_path.read_text(encoding="utf-8")

    assert "ck_dashboard_snapshots_avg_resume_score_range" in content
    assert "ck_user_analytics_request_counts_valid" in content
    assert "ck_activity_logs_activity_type_valid" in content
    assert "ck_activity_logs_entity_type_valid" in content


def test_analytics_migration_contains_indexes_and_fks() -> None:
    migration_path = Path(__file__).resolve().parents[1] / _MIGRATION_NAME
    content = migration_path.read_text(encoding="utf-8")

    assert "ix_dashboard_snapshots_user_id" in content
    assert "ix_activity_logs_user_created_at" in content
    assert '[["user_id"], ["users.id"]' not in content
    assert '["users.id"]' in content
