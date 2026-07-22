"""Persistence operations for dashboard snapshots."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cover_letter import CoverLetter
from app.models.dashboard_snapshot import DashboardSnapshot
from app.models.job_analysis import JobAnalysis
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.resume_tailoring_version import ResumeTailoringVersion
from app.models.tailoring_session import TailoringSession


class DashboardRepository:
    """Data-access operations for dashboard snapshots and aggregate metrics."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        total_resumes: int,
        total_resume_analyses: int,
        total_job_analyses: int,
        total_tailoring_sessions: int,
        average_resume_score: float | None,
        average_job_match_score: float | None,
        average_tailoring_score: float | None,
        generated_cover_letters: int,
    ) -> DashboardSnapshot:
        snapshot = DashboardSnapshot(
            user_id=user_id,
            total_resumes=total_resumes,
            total_resume_analyses=total_resume_analyses,
            total_job_analyses=total_job_analyses,
            total_tailoring_sessions=total_tailoring_sessions,
            average_resume_score=average_resume_score,
            average_job_match_score=average_job_match_score,
            average_tailoring_score=average_tailoring_score,
            generated_cover_letters=generated_cover_letters,
        )
        self._session.add(snapshot)
        await self._session.flush()
        await self._session.refresh(snapshot)
        return snapshot

    async def update(
        self,
        snapshot_id: UUID,
        *,
        total_resumes: int | None = None,
        total_resume_analyses: int | None = None,
        total_job_analyses: int | None = None,
        total_tailoring_sessions: int | None = None,
        average_resume_score: float | None = None,
        average_job_match_score: float | None = None,
        average_tailoring_score: float | None = None,
        generated_cover_letters: int | None = None,
    ) -> DashboardSnapshot | None:
        snapshot = await self.get_by_id(snapshot_id)
        if snapshot is None:
            return None

        if total_resumes is not None:
            snapshot.total_resumes = total_resumes
        if total_resume_analyses is not None:
            snapshot.total_resume_analyses = total_resume_analyses
        if total_job_analyses is not None:
            snapshot.total_job_analyses = total_job_analyses
        if total_tailoring_sessions is not None:
            snapshot.total_tailoring_sessions = total_tailoring_sessions
        if average_resume_score is not None:
            snapshot.average_resume_score = average_resume_score
        if average_job_match_score is not None:
            snapshot.average_job_match_score = average_job_match_score
        if average_tailoring_score is not None:
            snapshot.average_tailoring_score = average_tailoring_score
        if generated_cover_letters is not None:
            snapshot.generated_cover_letters = generated_cover_letters

        await self._session.flush()
        return await self.get_by_id(snapshot_id)

    async def delete(self, snapshot_id: UUID) -> bool:
        snapshot = await self.get_by_id(snapshot_id)
        if snapshot is None:
            return False
        await self._session.delete(snapshot)
        await self._session.flush()
        return True

    async def get_by_id(self, snapshot_id: UUID) -> DashboardSnapshot | None:
        result = await self._session.execute(
            select(DashboardSnapshot).where(DashboardSnapshot.id == snapshot_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> list[DashboardSnapshot]:
        result = await self._session.execute(
            select(DashboardSnapshot)
            .where(DashboardSnapshot.user_id == user_id)
            .order_by(
                DashboardSnapshot.created_at.desc(),
                DashboardSnapshot.updated_at.desc(),
                DashboardSnapshot.id.desc(),
            )
        )
        return list(result.scalars().all())

    async def latest_snapshot(self, user_id: UUID) -> DashboardSnapshot | None:
        result = await self._session.execute(
            select(DashboardSnapshot)
            .where(DashboardSnapshot.user_id == user_id)
            .order_by(
                DashboardSnapshot.created_at.desc(),
                DashboardSnapshot.updated_at.desc(),
                DashboardSnapshot.id.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def calculate_metrics(self, user_id: UUID) -> dict[str, int | float | None]:
        total_resumes = await self._scalar_int(
            select(func.count(Resume.id)).where(Resume.user_id == user_id)
        )
        total_resume_analyses = await self._scalar_int(
            select(func.count(ResumeAnalysis.id))
            .join(ResumeAnalysis.resume)
            .where(Resume.user_id == user_id)
        )
        total_job_analyses = await self._scalar_int(
            select(func.count(JobAnalysis.id))
            .join(JobAnalysis.resume)
            .where(Resume.user_id == user_id)
        )
        total_tailoring_sessions = await self._scalar_int(
            select(func.count(TailoringSession.id))
            .join(TailoringSession.resume)
            .where(Resume.user_id == user_id)
        )
        generated_cover_letters = await self._scalar_int(
            select(func.count(CoverLetter.id))
            .join(CoverLetter.tailoring_session)
            .join(TailoringSession.resume)
            .where(Resume.user_id == user_id)
        )

        avg_resume_score = await self._scalar_float(
            select(func.avg(ResumeAnalysis.resume_score))
            .join(ResumeAnalysis.resume)
            .where(
                Resume.user_id == user_id,
                ResumeAnalysis.resume_score.is_not(None),
            )
        )
        avg_job_match_score = await self._scalar_float(
            select(func.avg(JobAnalysis.match_score))
            .join(JobAnalysis.resume)
            .where(
                Resume.user_id == user_id,
                JobAnalysis.match_score.is_not(None),
            )
        )
        avg_tailoring_score = await self._scalar_float(
            select(func.avg(ResumeTailoringVersion.ats_score))
            .join(ResumeTailoringVersion.resume)
            .where(
                Resume.user_id == user_id,
                ResumeTailoringVersion.ats_score.is_not(None),
            )
        )

        return {
            "total_resumes": total_resumes,
            "total_resume_analyses": total_resume_analyses,
            "total_job_analyses": total_job_analyses,
            "total_tailoring_sessions": total_tailoring_sessions,
            "average_resume_score": avg_resume_score,
            "average_job_match_score": avg_job_match_score,
            "average_tailoring_score": avg_tailoring_score,
            "generated_cover_letters": generated_cover_letters,
        }

    async def _scalar_int(self, statement) -> int:
        result = await self._session.execute(statement)
        value = result.scalar_one()
        return int(value or 0)

    async def _scalar_float(self, statement) -> float | None:
        result = await self._session.execute(statement)
        value = result.scalar_one()
        return float(value) if value is not None else None
