"""TailoringSession ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.enums.tailoring import TailoringStatus

if TYPE_CHECKING:
    from app.models.cover_letter import CoverLetter
    from app.models.job_description import JobDescription
    from app.models.resume import Resume
    from app.models.resume_tailoring_version import ResumeTailoringVersion


class TailoringSession(UUIDMixin, TimestampMixin, Base):
    """A single AI tailoring run for a resume and job description pair."""

    __tablename__ = "tailoring_sessions"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_description_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=TailoringStatus.PENDING.value,
        index=True,
    )

    resume: Mapped["Resume"] = relationship(back_populates="tailoring_sessions")
    job_description: Mapped["JobDescription"] = relationship(
        back_populates="tailoring_sessions"
    )
    resume_version: Mapped["ResumeTailoringVersion | None"] = relationship(
        back_populates="tailoring_session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    cover_letter: Mapped["CoverLetter | None"] = relationship(
        back_populates="tailoring_session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
