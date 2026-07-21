"""ResumeKeyword ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.resume_analysis import ResumeAnalysis


class ResumeKeyword(UUIDMixin, TimestampMixin, Base):
    """A keyword extracted from a resume analysis."""

    __tablename__ = "resume_keywords"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resume_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)

    analysis: Mapped["ResumeAnalysis"] = relationship(back_populates="keywords")
