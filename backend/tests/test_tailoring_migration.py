from __future__ import annotations

from pathlib import Path


def test_tailoring_migration_contains_expected_tables_and_constraints() -> None:
    migration_path = Path(__file__).resolve().parents[1] / (
        "alembic/versions/20260722_0915_f8d1c3e2a9b4_add_resume_tailoring_domain_tables.py"
    )
    content = migration_path.read_text(encoding="utf-8")

    assert '"tailoring_sessions"' in content
    assert '"resume_tailoring_versions"' in content
    assert '"cover_letters"' in content
    assert "ck_tailoring_sessions_status_valid" in content
    assert "ck_resume_tailoring_versions_ats_score_range" in content


def test_tailoring_migration_contains_expected_indexes_and_fk_targets() -> None:
    migration_path = Path(__file__).resolve().parents[1] / (
        "alembic/versions/20260722_0915_f8d1c3e2a9b4_add_resume_tailoring_domain_tables.py"
    )
    content = migration_path.read_text(encoding="utf-8")

    assert "ix_tailoring_sessions_resume_id" in content
    assert "ix_tailoring_sessions_job_description_id" in content
    assert "ix_resume_tailoring_versions_tailoring_session_id" in content
    assert '["resumes.id"]' in content
    assert '["job_descriptions.id"]' in content
    assert '["tailoring_sessions.id"]' in content
