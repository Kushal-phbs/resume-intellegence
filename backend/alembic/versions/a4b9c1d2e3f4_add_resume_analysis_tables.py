"""add resume analysis tables

Revision ID: a4b9c1d2e3f4
Revises:
Create Date: 2026-07-21 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "a4b9c1d2e3f4"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resume_analyses",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
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
        sa.Column("resume_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_version_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_status", sa.String(length=32), nullable=False),
        sa.Column("resume_score", sa.Integer(), nullable=True),
        sa.Column("ats_score", sa.Integer(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("llm_model", sa.String(length=255), nullable=True),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["resume_version_id"], ["resume_versions.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_resume_analyses_resume_id", "resume_analyses", ["resume_id"], unique=False
    )
    op.create_index(
        "ix_resume_analyses_resume_version_id",
        "resume_analyses",
        ["resume_version_id"],
        unique=False,
    )
    op.create_index(
        "ix_resume_analyses_analysis_status",
        "resume_analyses",
        ["analysis_status"],
        unique=False,
    )

    op.create_table(
        "resume_skills",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
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
        sa.Column("analysis_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["resume_analyses.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_resume_skills_analysis_id", "resume_skills", ["analysis_id"], unique=False
    )

    op.create_table(
        "resume_keywords",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
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
        sa.Column("analysis_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("keyword", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["resume_analyses.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_resume_keywords_analysis_id",
        "resume_keywords",
        ["analysis_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_resume_keywords_analysis_id", table_name="resume_keywords")
    op.drop_table("resume_keywords")
    op.drop_index("ix_resume_skills_analysis_id", table_name="resume_skills")
    op.drop_table("resume_skills")
    op.drop_index("ix_resume_analyses_analysis_status", table_name="resume_analyses")
    op.drop_index("ix_resume_analyses_resume_version_id", table_name="resume_analyses")
    op.drop_index("ix_resume_analyses_resume_id", table_name="resume_analyses")
    op.drop_table("resume_analyses")
