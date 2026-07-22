"""ActivityLog ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class ActivityLog(UUIDMixin, Base):
    """Immutable activity event row used for dashboard timelines."""

    __tablename__ = "activity_logs"
    __table_args__ = (
        CheckConstraint(
            "activity_type IN ("
            "'resume_uploaded',"
            "'resume_analyzed',"
            "'job_analyzed',"
            "'resume_tailored',"
            "'cover_letter_generated',"
            "'export_generated',"
            "'login'"
            ")",
            name="ck_activity_logs_activity_type_valid",
        ),
        CheckConstraint(
            "entity_type IN ("
            "'resume',"
            "'analysis',"
            "'job',"
            "'tailoring',"
            "'cover_letter',"
            "'export'"
            ")",
            name="ck_activity_logs_entity_type_valid",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        index=True,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship(back_populates="activity_logs")
