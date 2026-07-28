"""UserAnalytics ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserAnalytics(UUIDMixin, TimestampMixin, Base):
    """Rolling analytics counters and latency metrics per user."""

    __tablename__ = "user_analytics"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_analytics_user_id"),
        CheckConstraint(
            "total_ai_requests >= 0",
            name="ck_user_analytics_total_ai_requests",
        ),
        CheckConstraint(
            "total_tokens_used >= 0",
            name="ck_user_analytics_total_tokens_used",
        ),
        CheckConstraint(
            "successful_requests >= 0",
            name="ck_user_analytics_successful_requests",
        ),
        CheckConstraint(
            "failed_requests >= 0",
            name="ck_user_analytics_failed_requests",
        ),
        CheckConstraint(
            "average_processing_time_ms IS NULL OR average_processing_time_ms >= 0",
            name="ck_user_analytics_avg_processing_time_non_negative",
        ),
        CheckConstraint(
            "successful_requests + failed_requests <= total_ai_requests",
            name="ck_user_analytics_request_counts_valid",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    total_ai_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_processing_time_ms: Mapped[float | None] = mapped_column(Float)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="user_analytics")
