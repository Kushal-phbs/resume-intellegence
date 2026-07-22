"""KeywordMatch ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.job_analysis import JobAnalysis


class KeywordMatch(UUIDMixin, TimestampMixin, Base):
    """Keyword identified as matched between resume and job description."""

    __tablename__ = "keyword_matches"

    job_analysis_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("job_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)

    job_analysis: Mapped["JobAnalysis"] = relationship(back_populates="keyword_matches")
