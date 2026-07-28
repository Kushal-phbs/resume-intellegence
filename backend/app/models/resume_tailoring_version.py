"""ResumeTailoringVersion ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.resume import Resume
    from app.models.tailoring_session import TailoringSession


class ResumeTailoringVersion(UUIDMixin, TimestampMixin, Base):
    """A tailored resume version generated inside a tailoring session."""

    __tablename__ = "resume_tailoring_versions"
    __table_args__ = (
        UniqueConstraint(
            "tailoring_session_id", name="uq_resume_tailoring_versions_session_id"
        ),
    )

    resume_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tailoring_session_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tailoring_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    professional_summary: Mapped[str] = mapped_column(Text, nullable=False)
    experience_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    skills_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    ats_score: Mapped[int] = mapped_column(Integer, nullable=False)
    recommendations_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    resume: Mapped["Resume"] = relationship(back_populates="tailoring_resume_versions")
    tailoring_session: Mapped["TailoringSession"] = relationship(
        back_populates="resume_version"
    )
