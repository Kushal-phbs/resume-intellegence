from __future__ import annotations

from pathlib import Path

from app.models.job_analysis import JobAnalysis


def test_job_analysis_model_has_integrity_check_constraints() -> None:
    table_args = JobAnalysis.__table_args__
    names = {constraint.name for constraint in table_args}

    assert "ck_job_analyses_match_score_range" in names
    assert "ck_job_analyses_ats_match_score_range" in names
    assert "ck_job_analyses_analysis_status_valid" in names


def test_job_analysis_constraints_migration_contains_required_checks() -> None:
    migration_path = Path(__file__).resolve().parents[1] / (
        "alembic/versions/20260721_2355_4c2d9b7e1a88_add_job_analysis_constraints.py"
    )
    content = migration_path.read_text(encoding="utf-8")

    assert "ck_job_analyses_match_score_range" in content
    assert "match_score >= 0 AND match_score <= 100" in content
    assert "ck_job_analyses_ats_match_score_range" in content
    assert "ats_match_score >= 0 AND ats_match_score <= 100" in content
    assert "ck_job_analyses_analysis_status_valid" in content
    assert (
        "analysis_status IN ('pending', 'processing', 'completed', 'failed')" in content
    )
