"""Persistence operations for job analysis entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import load_only, selectinload

from app.db.session import AsyncSessionLocal
from app.dto.job_analysis import JobAnalysisResult
from app.enums import JobAnalysisStatus
from app.models import Resume
from app.models.job_analysis import JobAnalysis
from app.models.keyword_match import KeywordMatch
from app.models.matched_skill import MatchedSkill
from app.models.missing_skill import MissingSkill


class JobAnalysisRepository:
    """Data-access operations for job analysis records and children."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal,
    ) -> None:
        self._session = session
        self._session_factory = session_factory

    async def create(
        self,
        *,
        resume_id: UUID,
        job_description_id: UUID,
        analysis_status: JobAnalysisStatus | str = JobAnalysisStatus.PENDING,
    ) -> JobAnalysis:
        """Create and persist a job analysis row."""
        analysis = JobAnalysis(
            resume_id=resume_id,
            job_description_id=job_description_id,
            analysis_status=(
                analysis_status.value
                if isinstance(analysis_status, JobAnalysisStatus)
                else analysis_status
            ),
            strengths=[],
            weaknesses=[],
            recommendations=[],
        )
        self._session.add(analysis)
        await self._session.flush()
        await self._session.refresh(analysis)
        return analysis

    async def update(
        self,
        analysis_id: UUID,
        *,
        result: JobAnalysisResult,
        analysis_status: JobAnalysisStatus = JobAnalysisStatus.COMPLETED,
        llm_model: str | None = None,
        raw_response: str | None = None,
        error_message: str | None = None,
    ) -> JobAnalysis | None:
        """Update a stored job analysis row from a typed analysis result."""
        analysis = await self.get_by_id(analysis_id)
        if analysis is None:
            return None

        analysis.analysis_status = analysis_status.value
        analysis.match_score = result.overall_match
        analysis.ats_match_score = result.ats_match
        analysis.summary = result.summary
        analysis.strengths = result.strengths
        analysis.weaknesses = result.weaknesses
        analysis.recommendations = result.recommendations
        analysis.llm_model = llm_model
        analysis.raw_response = raw_response
        analysis.error_message = error_message

        analysis.matched_skills = [
            MatchedSkill(job_analysis_id=analysis_id, skill_name=skill)
            for skill in result.matched_skills
        ]
        analysis.missing_skills = [
            MissingSkill(job_analysis_id=analysis_id, skill_name=skill)
            for skill in result.missing_skills
        ]
        analysis.keyword_matches = [
            KeywordMatch(job_analysis_id=analysis_id, keyword=keyword)
            for keyword in result.keyword_matches
        ]

        await self._session.flush()
        return await self.get_by_id(analysis_id)

    async def get_by_id(self, analysis_id: UUID) -> JobAnalysis | None:
        """Return a job analysis by UUID."""
        result = await self._session.execute(
            select(JobAnalysis)
            .options(
                selectinload(JobAnalysis.resume),
                selectinload(JobAnalysis.job_description),
                selectinload(JobAnalysis.matched_skills),
                selectinload(JobAnalysis.missing_skills),
                selectinload(JobAnalysis.keyword_matches),
            )
            .where(JobAnalysis.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> list[JobAnalysis]:
        """Return all job analyses for resumes owned by a user."""
        result = await self._session.execute(
            select(JobAnalysis)
            .join(JobAnalysis.resume)
            .options(
                selectinload(JobAnalysis.resume),
                selectinload(JobAnalysis.job_description),
                selectinload(JobAnalysis.matched_skills),
                selectinload(JobAnalysis.missing_skills),
                selectinload(JobAnalysis.keyword_matches),
            )
            .where(Resume.user_id == user_id)
            .order_by(
                JobAnalysis.created_at.desc(),
                JobAnalysis.updated_at.desc(),
                JobAnalysis.id.desc(),
            )
        )
        return list(result.scalars().all())

    async def list_history_by_user(self, user_id: UUID) -> list[JobAnalysis]:
        """Return summary-ready analyses for one user without child collections."""
        result = await self._session.execute(
            select(JobAnalysis)
            .join(JobAnalysis.resume)
            .options(
                load_only(
                    JobAnalysis.id,
                    JobAnalysis.resume_id,
                    JobAnalysis.job_description_id,
                    JobAnalysis.analysis_status,
                    JobAnalysis.match_score,
                    JobAnalysis.ats_match_score,
                    JobAnalysis.strengths,
                    JobAnalysis.weaknesses,
                    JobAnalysis.recommendations,
                    JobAnalysis.created_at,
                    JobAnalysis.updated_at,
                    JobAnalysis.error_message,
                )
            )
            .where(Resume.user_id == user_id)
            .order_by(
                JobAnalysis.created_at.desc(),
                JobAnalysis.updated_at.desc(),
                JobAnalysis.id.desc(),
            )
        )
        return list(result.scalars().all())

    async def delete(self, analysis_id: UUID) -> bool:
        """Delete a stored job analysis row."""
        analysis = await self.get_by_id(analysis_id)
        if analysis is None:
            return False
        await self._session.delete(analysis)
        await self._session.flush()
        return True

    async def persist_failed_committed(
        self,
        *,
        analysis_id: UUID,
        resume_id: UUID,
        job_description_id: UUID,
        result: JobAnalysisResult,
        llm_model: str | None,
        raw_response: str | None,
        error_message: str,
    ) -> None:
        """Persist FAILED analysis state in an independent committed transaction."""
        async with self._session_factory() as session:
            repo = JobAnalysisRepository(session, session_factory=self._session_factory)
            analysis = await repo.get_by_id(analysis_id)
            if analysis is None:
                analysis = JobAnalysis(
                    id=analysis_id,
                    resume_id=resume_id,
                    job_description_id=job_description_id,
                    analysis_status=JobAnalysisStatus.FAILED.value,
                    strengths=[],
                    weaknesses=[],
                    recommendations=[],
                )
                session.add(analysis)
                await session.flush()

            analysis.analysis_status = JobAnalysisStatus.FAILED.value
            analysis.match_score = result.overall_match
            analysis.ats_match_score = result.ats_match
            analysis.summary = result.summary
            analysis.strengths = result.strengths
            analysis.weaknesses = result.weaknesses
            analysis.recommendations = result.recommendations
            analysis.llm_model = llm_model
            analysis.raw_response = raw_response
            analysis.error_message = error_message
            analysis.matched_skills = []
            analysis.missing_skills = []
            analysis.keyword_matches = []

            await session.flush()
            await session.commit()
