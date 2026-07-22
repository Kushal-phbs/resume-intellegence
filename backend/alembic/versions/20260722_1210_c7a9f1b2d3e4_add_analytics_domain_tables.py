"""add analytics domain tables

Revision ID: c7a9f1b2d3e4
Revises: f8d1c3e2a9b4
Create Date: 2026-07-22 12:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7a9f1b2d3e4"
down_revision: Union[str, None] = "f8d1c3e2a9b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dashboard_snapshots",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("total_resumes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "total_resume_analyses",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_job_analyses", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "total_tailoring_sessions",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("average_resume_score", sa.Float(), nullable=True),
        sa.Column("average_job_match_score", sa.Float(), nullable=True),
        sa.Column("average_tailoring_score", sa.Float(), nullable=True),
        sa.Column(
            "generated_cover_letters",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
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
            "total_resumes >= 0", name="ck_dashboard_snapshots_total_resumes"
        ),
        sa.CheckConstraint(
            "total_resume_analyses >= 0",
            name="ck_dashboard_snapshots_total_resume_analyses",
        ),
        sa.CheckConstraint(
            "total_job_analyses >= 0",
            name="ck_dashboard_snapshots_total_job_analyses",
        ),
        sa.CheckConstraint(
            "total_tailoring_sessions >= 0",
            name="ck_dashboard_snapshots_total_tailoring_sessions",
        ),
        sa.CheckConstraint(
            "generated_cover_letters >= 0",
            name="ck_dashboard_snapshots_generated_cover_letters",
        ),
        sa.CheckConstraint(
            "average_resume_score IS NULL OR "
            "(average_resume_score >= 0 AND average_resume_score <= 100)",
            name="ck_dashboard_snapshots_avg_resume_score_range",
        ),
        sa.CheckConstraint(
            "average_job_match_score IS NULL OR "
            "(average_job_match_score >= 0 AND average_job_match_score <= 100)",
            name="ck_dashboard_snapshots_avg_job_match_score_range",
        ),
        sa.CheckConstraint(
            "average_tailoring_score IS NULL OR "
            "(average_tailoring_score >= 0 AND average_tailoring_score <= 100)",
            name="ck_dashboard_snapshots_avg_tailoring_score_range",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_dashboard_snapshots_user_id"),
        "dashboard_snapshots",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_dashboard_snapshots_user_created_at",
        "dashboard_snapshots",
        ["user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "user_analytics",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "total_ai_requests",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_tokens_used",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "successful_requests",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "failed_requests",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("average_processing_time_ms", sa.Float(), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
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
            "total_ai_requests >= 0",
            name="ck_user_analytics_total_ai_requests",
        ),
        sa.CheckConstraint(
            "total_tokens_used >= 0",
            name="ck_user_analytics_total_tokens_used",
        ),
        sa.CheckConstraint(
            "successful_requests >= 0",
            name="ck_user_analytics_successful_requests",
        ),
        sa.CheckConstraint(
            "failed_requests >= 0",
            name="ck_user_analytics_failed_requests",
        ),
        sa.CheckConstraint(
            "average_processing_time_ms IS NULL OR average_processing_time_ms >= 0",
            name="ck_user_analytics_avg_processing_time_non_negative",
        ),
        sa.CheckConstraint(
            "successful_requests + failed_requests <= total_ai_requests",
            name="ck_user_analytics_request_counts_valid",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_analytics_user_id"),
    )
    op.create_index(
        op.f("ix_user_analytics_user_id"),
        "user_analytics",
        ["user_id"],
        unique=True,
    )

    op.create_table(
        "activity_logs",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("activity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "activity_type IN ('resume_uploaded', 'resume_analyzed', 'job_analyzed', "
            "'resume_tailored', 'cover_letter_generated', 'export_generated', 'login')",
            name="ck_activity_logs_activity_type_valid",
        ),
        sa.CheckConstraint(
            "entity_type IN ('resume', 'analysis', 'job', 'tailoring', "
            "'cover_letter', 'export')",
            name="ck_activity_logs_entity_type_valid",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_activity_logs_user_id"),
        "activity_logs",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_activity_logs_activity_type"),
        "activity_logs",
        ["activity_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_activity_logs_entity_type"),
        "activity_logs",
        ["entity_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_activity_logs_entity_id"),
        "activity_logs",
        ["entity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_activity_logs_created_at"),
        "activity_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_activity_logs_user_created_at",
        "activity_logs",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_activity_logs_user_created_at", table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_created_at"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_entity_id"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_entity_type"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_activity_type"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_user_id"), table_name="activity_logs")
    op.drop_table("activity_logs")

    op.drop_index(op.f("ix_user_analytics_user_id"), table_name="user_analytics")
    op.drop_table("user_analytics")

    op.drop_index(
        "ix_dashboard_snapshots_user_created_at",
        table_name="dashboard_snapshots",
    )
    op.drop_index(
        op.f("ix_dashboard_snapshots_user_id"),
        table_name="dashboard_snapshots",
    )
    op.drop_table("dashboard_snapshots")
