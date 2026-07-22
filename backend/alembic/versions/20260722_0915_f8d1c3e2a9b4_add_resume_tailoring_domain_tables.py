"""add resume tailoring domain tables

Revision ID: f8d1c3e2a9b4
Revises: 4c2d9b7e1a88
Create Date: 2026-07-22 09:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f8d1c3e2a9b4"
down_revision: Union[str, None] = "4c2d9b7e1a88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tailoring_sessions",
        sa.Column("resume_id", sa.UUID(), nullable=False),
        sa.Column("job_description_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
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
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_tailoring_sessions_status_valid",
        ),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["job_description_id"], ["job_descriptions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tailoring_sessions_resume_id"),
        "tailoring_sessions",
        ["resume_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tailoring_sessions_job_description_id"),
        "tailoring_sessions",
        ["job_description_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tailoring_sessions_status"),
        "tailoring_sessions",
        ["status"],
        unique=False,
    )

    op.create_table(
        "resume_tailoring_versions",
        sa.Column("resume_id", sa.UUID(), nullable=False),
        sa.Column("tailoring_session_id", sa.UUID(), nullable=False),
        sa.Column("professional_summary", sa.Text(), nullable=False),
        sa.Column("experience_json", sa.JSON(), nullable=False),
        sa.Column("skills_json", sa.JSON(), nullable=False),
        sa.Column("ats_score", sa.Integer(), nullable=False),
        sa.Column("recommendations_json", sa.JSON(), nullable=False),
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
        sa.CheckConstraint(
            "ats_score >= 0 AND ats_score <= 100",
            name="ck_resume_tailoring_versions_ats_score_range",
        ),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tailoring_session_id"], ["tailoring_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tailoring_session_id", name="uq_resume_tailoring_versions_session_id"
        ),
    )
    op.create_index(
        op.f("ix_resume_tailoring_versions_resume_id"),
        "resume_tailoring_versions",
        ["resume_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_resume_tailoring_versions_tailoring_session_id"),
        "resume_tailoring_versions",
        ["tailoring_session_id"],
        unique=True,
    )

    op.create_table(
        "cover_letters",
        sa.Column("tailoring_session_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("greeting", sa.Text(), nullable=False),
        sa.Column("introduction", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("closing", sa.Text(), nullable=False),
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
            ["tailoring_session_id"], ["tailoring_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tailoring_session_id", name="uq_cover_letters_session_id"),
    )
    op.create_index(
        op.f("ix_cover_letters_tailoring_session_id"),
        "cover_letters",
        ["tailoring_session_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_cover_letters_tailoring_session_id"), table_name="cover_letters"
    )
    op.drop_table("cover_letters")

    op.drop_index(
        op.f("ix_resume_tailoring_versions_tailoring_session_id"),
        table_name="resume_tailoring_versions",
    )
    op.drop_index(
        op.f("ix_resume_tailoring_versions_resume_id"),
        table_name="resume_tailoring_versions",
    )
    op.drop_table("resume_tailoring_versions")

    op.drop_index(op.f("ix_tailoring_sessions_status"), table_name="tailoring_sessions")
    op.drop_index(
        op.f("ix_tailoring_sessions_job_description_id"),
        table_name="tailoring_sessions",
    )
    op.drop_index(
        op.f("ix_tailoring_sessions_resume_id"), table_name="tailoring_sessions"
    )
    op.drop_table("tailoring_sessions")
