"""add job intelligence tables

Revision ID: b91e5a7c4d11
Revises: 39dfbcd9dddc
Create Date: 2026-07-21 22:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b91e5a7c4d11"
down_revision: Union[str, None] = "39dfbcd9dddc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_analyses",
        sa.Column("resume_id", sa.UUID(), nullable=False),
        sa.Column("job_description_id", sa.UUID(), nullable=False),
        sa.Column("analysis_status", sa.String(length=32), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=True),
        sa.Column("ats_match_score", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("llm_model", sa.String(length=255), nullable=True),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_description_id"], ["job_descriptions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_job_analyses_analysis_status"),
        "job_analyses",
        ["analysis_status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_job_analyses_job_description_id"),
        "job_analyses",
        ["job_description_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_job_analyses_resume_id"),
        "job_analyses",
        ["resume_id"],
        unique=False,
    )

    op.create_table(
        "matched_skills",
        sa.Column("job_analysis_id", sa.UUID(), nullable=False),
        sa.Column("skill_name", sa.String(length=255), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_analysis_id"], ["job_analyses.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_matched_skills_job_analysis_id"),
        "matched_skills",
        ["job_analysis_id"],
        unique=False,
    )

    op.create_table(
        "missing_skills",
        sa.Column("job_analysis_id", sa.UUID(), nullable=False),
        sa.Column("skill_name", sa.String(length=255), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_analysis_id"], ["job_analyses.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_missing_skills_job_analysis_id"),
        "missing_skills",
        ["job_analysis_id"],
        unique=False,
    )

    op.create_table(
        "keyword_matches",
        sa.Column("job_analysis_id", sa.UUID(), nullable=False),
        sa.Column("keyword", sa.String(length=255), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_analysis_id"], ["job_analyses.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_keyword_matches_job_analysis_id"),
        "keyword_matches",
        ["job_analysis_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_keyword_matches_job_analysis_id"), table_name="keyword_matches"
    )
    op.drop_table("keyword_matches")

    op.drop_index(
        op.f("ix_missing_skills_job_analysis_id"), table_name="missing_skills"
    )
    op.drop_table("missing_skills")

    op.drop_index(
        op.f("ix_matched_skills_job_analysis_id"), table_name="matched_skills"
    )
    op.drop_table("matched_skills")

    op.drop_index(op.f("ix_job_analyses_resume_id"), table_name="job_analyses")
    op.drop_index(op.f("ix_job_analyses_job_description_id"), table_name="job_analyses")
    op.drop_index(op.f("ix_job_analyses_analysis_status"), table_name="job_analyses")
    op.drop_table("job_analyses")
