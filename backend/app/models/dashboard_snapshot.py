"""DashboardSnapshot ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class DashboardSnapshot(UUIDMixin, TimestampMixin, Base):
    """Point-in-time dashboard metrics snapshot for one user."""

    __tablename__ = "dashboard_snapshots"
    __table_args__ = (
        Index("ix_dashboard_snapshots_user_created_at", "user_id", "created_at"),
        CheckConstraint(
            "total_resumes >= 0",
            name="ck_dashboard_snapshots_total_resumes",
        ),
        CheckConstraint(
            "total_resume_analyses >= 0",
            name="ck_dashboard_snapshots_total_resume_analyses",
        ),
        CheckConstraint(
            "total_job_analyses >= 0",
            name="ck_dashboard_snapshots_total_job_analyses",
        ),
        CheckConstraint(
            "total_tailoring_sessions >= 0",
            name="ck_dashboard_snapshots_total_tailoring_sessions",
        ),
        CheckConstraint(
            "generated_cover_letters >= 0",
            name="ck_dashboard_snapshots_generated_cover_letters",
        ),
        CheckConstraint(
            "average_resume_score IS NULL OR "
            "(average_resume_score >= 0 AND average_resume_score <= 100)",
            name="ck_dashboard_snapshots_avg_resume_score_range",
        ),
        CheckConstraint(
            "average_job_match_score IS NULL OR "
            "(average_job_match_score >= 0 AND average_job_match_score <= 100)",
            name="ck_dashboard_snapshots_avg_job_match_score_range",
        ),
        CheckConstraint(
            "average_tailoring_score IS NULL OR "
            "(average_tailoring_score >= 0 AND average_tailoring_score <= 100)",
            name="ck_dashboard_snapshots_avg_tailoring_score_range",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total_resumes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_resume_analyses: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_job_analyses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tailoring_sessions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    average_resume_score: Mapped[float | None] = mapped_column(Float)
    average_job_match_score: Mapped[float | None] = mapped_column(Float)
    average_tailoring_score: Mapped[float | None] = mapped_column(Float)
    generated_cover_letters: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    user: Mapped["User"] = relationship(back_populates="dashboard_snapshots")
