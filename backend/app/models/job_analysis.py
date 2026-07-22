"""JobAnalysis ORM model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.enums import JobAnalysisStatus

if TYPE_CHECKING:
    from app.models.job_description import JobDescription
    from app.models.keyword_match import KeywordMatch
    from app.models.matched_skill import MatchedSkill
    from app.models.missing_skill import MissingSkill
    from app.models.resume import Resume


class JobAnalysis(UUIDMixin, TimestampMixin, Base):
    """A persisted resume-vs-job matching analysis run."""

    __tablename__ = "job_analyses"
    __table_args__ = (
        CheckConstraint(
            "match_score IS NULL OR (match_score >= 0 AND match_score <= 100)",
            name="ck_job_analyses_match_score_range",
        ),
        CheckConstraint(
            "ats_match_score IS NULL OR "
            "(ats_match_score >= 0 AND ats_match_score <= 100)",
            name="ck_job_analyses_ats_match_score_range",
        ),
        CheckConstraint(
            "analysis_status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_job_analyses_analysis_status_valid",
        ),
    )

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
    analysis_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=JobAnalysisStatus.PENDING.value,
        index=True,
    )
    match_score: Mapped[int | None] = mapped_column(Integer)
    ats_match_score: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[str | None] = mapped_column(Text)
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    recommendations: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    llm_model: Mapped[str | None] = mapped_column(String(255))
    raw_response: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)

    resume: Mapped["Resume"] = relationship(back_populates="job_analyses")
    job_description: Mapped["JobDescription"] = relationship(
        back_populates="job_analyses"
    )
    matched_skills: Mapped[list["MatchedSkill"]] = relationship(
        back_populates="job_analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MatchedSkill.skill_name",
    )
    missing_skills: Mapped[list["MissingSkill"]] = relationship(
        back_populates="job_analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MissingSkill.skill_name",
    )
    keyword_matches: Mapped[list["KeywordMatch"]] = relationship(
        back_populates="job_analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="KeywordMatch.keyword",
    )
