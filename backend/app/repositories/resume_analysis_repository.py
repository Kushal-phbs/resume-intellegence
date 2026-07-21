"""Persistence operations for resume analysis entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dto.analysis import AnalysisResult
from app.enums import AnalysisStatus
from app.models.resume_analysis import ResumeAnalysis
from app.models.resume_keyword import ResumeKeyword
from app.models.resume_skill import ResumeSkill


class ResumeAnalysisRepository:
    """Data-access operations for resume analysis records and children."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        resume_id: UUID,
        resume_version_id: UUID,
        analysis_status: AnalysisStatus | str = AnalysisStatus.PENDING,
        resume_score: int | None = None,
        ats_score: int | None = None,
        strengths: list[str] | None = None,
        weaknesses: list[str] | None = None,
        recommendations: list[str] | None = None,
        extracted_text: str | None = None,
        llm_model: str | None = None,
        raw_response: str | None = None,
        error_message: str | None = None,
    ) -> ResumeAnalysis:
        """Create and persist a resume analysis row."""
        analysis = ResumeAnalysis(
            resume_id=resume_id,
            resume_version_id=resume_version_id,
            analysis_status=(
                analysis_status.value
                if isinstance(analysis_status, AnalysisStatus)
                else analysis_status
            ),
            resume_score=resume_score,
            ats_score=ats_score,
            strengths=strengths or [],
            weaknesses=weaknesses or [],
            recommendations=recommendations or [],
            extracted_text=extracted_text,
            llm_model=llm_model,
            raw_response=raw_response,
            error_message=error_message,
        )
        self._session.add(analysis)
        await self._session.flush()
        await self._session.refresh(analysis)
        return analysis

    async def update(
        self,
        analysis_id: UUID,
        *,
        result: AnalysisResult,
        analysis_status: AnalysisStatus = AnalysisStatus.COMPLETED,
        llm_model: str | None = None,
        raw_response: str | None = None,
        error_message: str | None = None,
    ) -> ResumeAnalysis | None:
        """Update a stored analysis row from a typed analysis result.

        Args:
            analysis_id: Analysis primary key.
            result: Typed analysis data parsed from the LLM response.
            analysis_status: New lifecycle status set by the service layer.
            llm_model: Model identifier returned by the LLM provider.
            raw_response: Raw LLM response payload for diagnostics.
            error_message: Failure message when persisting a failed analysis.

        Returns:
            The refreshed analysis entity, or ``None`` when the row is missing.
        """
        analysis = await self.get_by_id(analysis_id)
        if analysis is None:
            return None

        analysis.analysis_status = analysis_status.value
        analysis.resume_score = result.resume_score
        analysis.ats_score = result.ats_score
        analysis.strengths = result.strengths
        analysis.weaknesses = result.weaknesses
        analysis.recommendations = result.recommendations
        analysis.llm_model = llm_model
        analysis.raw_response = raw_response
        analysis.error_message = error_message

        analysis.skills = [
            ResumeSkill(
                analysis_id=analysis_id,
                skill_name=skill.skill_name,
                category=skill.category.value,
            )
            for skill in result.skills
        ]
        analysis.keywords = [
            ResumeKeyword(analysis_id=analysis_id, keyword=keyword)
            for keyword in result.keywords
        ]

        await self._session.flush()
        return await self.get_by_id(analysis_id)

    async def get_latest(self, resume_id: UUID) -> ResumeAnalysis | None:
        """Return the most recent analysis for a resume, if any."""
        result = await self._session.execute(
            select(ResumeAnalysis)
            .options(
                selectinload(ResumeAnalysis.skills),
                selectinload(ResumeAnalysis.keywords),
            )
            .where(ResumeAnalysis.resume_id == resume_id)
            .order_by(
                ResumeAnalysis.created_at.desc(),
                ResumeAnalysis.updated_at.desc(),
                ResumeAnalysis.id.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_completed(self, resume_id: UUID) -> ResumeAnalysis | None:
        """Return the most recent completed analysis for a resume, if any."""
        result = await self._session.execute(
            select(ResumeAnalysis)
            .options(
                selectinload(ResumeAnalysis.skills),
                selectinload(ResumeAnalysis.keywords),
            )
            .where(
                ResumeAnalysis.resume_id == resume_id,
                ResumeAnalysis.analysis_status == AnalysisStatus.COMPLETED.value,
            )
            .order_by(
                ResumeAnalysis.created_at.desc(),
                ResumeAnalysis.updated_at.desc(),
                ResumeAnalysis.id.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_active_by_resume(self, resume_id: UUID) -> ResumeAnalysis | None:
        """Return an in-progress analysis for a resume, if any."""
        result = await self._session.execute(
            select(ResumeAnalysis)
            .where(
                ResumeAnalysis.resume_id == resume_id,
                ResumeAnalysis.analysis_status == AnalysisStatus.PROCESSING.value,
            )
            .order_by(
                ResumeAnalysis.created_at.desc(),
                ResumeAnalysis.updated_at.desc(),
                ResumeAnalysis.id.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_resume(self, resume_id: UUID) -> list[ResumeAnalysis]:
        """Return all analyses for a resume, newest first."""
        result = await self._session.execute(
            select(ResumeAnalysis)
            .options(
                selectinload(ResumeAnalysis.skills),
                selectinload(ResumeAnalysis.keywords),
            )
            .where(ResumeAnalysis.resume_id == resume_id)
            .order_by(
                ResumeAnalysis.created_at.desc(),
                ResumeAnalysis.updated_at.desc(),
                ResumeAnalysis.id.desc(),
            )
        )
        return list(result.scalars().all())

    async def delete(self, analysis_id: UUID) -> bool:
        """Delete a stored analysis row."""
        analysis = await self.get_by_id(analysis_id)
        if analysis is None:
            return False
        await self._session.delete(analysis)
        await self._session.flush()
        return True

    async def get_by_id(self, analysis_id: UUID) -> ResumeAnalysis | None:
        """Return a resume analysis by UUID."""
        result = await self._session.execute(
            select(ResumeAnalysis)
            .options(
                selectinload(ResumeAnalysis.resume),
                selectinload(ResumeAnalysis.skills),
                selectinload(ResumeAnalysis.keywords),
            )
            .where(ResumeAnalysis.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def clear_by_resume(self, resume_id: UUID) -> int:
        """Delete all analysis rows for a resume.

        Returns the number of rows removed.
        """
        result = await self._session.execute(
            delete(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)
        )
        await self._session.flush()
        return result.rowcount or 0
