"""ResumeAnalysis ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.enums import AnalysisStatus

if TYPE_CHECKING:
    from app.models.resume import Resume
    from app.models.resume_keyword import ResumeKeyword
    from app.models.resume_skill import ResumeSkill
    from app.models.resume_version import ResumeVersion


class ResumeAnalysis(UUIDMixin, TimestampMixin, Base):
    """A persisted analysis run for a specific resume version."""

    __tablename__ = "resume_analyses"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_version_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resume_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=AnalysisStatus.PENDING.value,
        index=True,
    )
    resume_score: Mapped[int | None] = mapped_column(Integer)
    ats_score: Mapped[int | None] = mapped_column(Integer)
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    recommendations: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    extracted_text: Mapped[str | None] = mapped_column(Text)
    llm_model: Mapped[str | None] = mapped_column(String(255))
    raw_response: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)

    resume: Mapped["Resume"] = relationship(back_populates="analyses")
    resume_version: Mapped["ResumeVersion"] = relationship(back_populates="analyses")
    skills: Mapped[list["ResumeSkill"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ResumeSkill.skill_name",
    )
    keywords: Mapped[list["ResumeKeyword"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ResumeKeyword.keyword",
    )
