"""add job analysis integrity constraints

Revision ID: 4c2d9b7e1a88
Revises: b91e5a7c4d11
Create Date: 2026-07-21 23:55:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "4c2d9b7e1a88"
down_revision: Union[str, None] = "b91e5a7c4d11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_job_analyses_match_score_range",
        "job_analyses",
        "match_score IS NULL OR (match_score >= 0 AND match_score <= 100)",
    )
    op.create_check_constraint(
        "ck_job_analyses_ats_match_score_range",
        "job_analyses",
        "ats_match_score IS NULL OR (ats_match_score >= 0 AND ats_match_score <= 100)",
    )
    op.create_check_constraint(
        "ck_job_analyses_analysis_status_valid",
        "job_analyses",
        "analysis_status IN ('pending', 'processing', 'completed', 'failed')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_job_analyses_analysis_status_valid",
        "job_analyses",
        type_="check",
    )
    op.drop_constraint(
        "ck_job_analyses_ats_match_score_range",
        "job_analyses",
        type_="check",
    )
    op.drop_constraint(
        "ck_job_analyses_match_score_range",
        "job_analyses",
        type_="check",
    )
