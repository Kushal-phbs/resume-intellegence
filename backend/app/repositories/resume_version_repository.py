"""Persistence operations for tailored resume versions."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.resume_tailoring_version import ResumeTailoringVersion


class ResumeVersionRepository:
    """Data-access operations for tailored resume versions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        resume_id: UUID,
        tailoring_session_id: UUID,
        professional_summary: str,
        experience_json: list[dict[str, object]],
        skills_json: list[dict[str, object]],
        ats_score: int,
        recommendations_json: list[dict[str, object]],
    ) -> ResumeTailoringVersion:
        version = ResumeTailoringVersion(
            resume_id=resume_id,
            tailoring_session_id=tailoring_session_id,
            professional_summary=professional_summary,
            experience_json=experience_json,
            skills_json=skills_json,
            ats_score=ats_score,
            recommendations_json=recommendations_json,
        )
        self._session.add(version)
        await self._session.flush()
        await self._session.refresh(version)
        return version

    async def update(
        self,
        version_id: UUID,
        *,
        professional_summary: str | None = None,
        experience_json: list[dict[str, object]] | None = None,
        skills_json: list[dict[str, object]] | None = None,
        ats_score: int | None = None,
        recommendations_json: list[dict[str, object]] | None = None,
    ) -> ResumeTailoringVersion | None:
        version = await self.get_by_id(version_id)
        if version is None:
            return None

        if professional_summary is not None:
            version.professional_summary = professional_summary
        if experience_json is not None:
            version.experience_json = experience_json
        if skills_json is not None:
            version.skills_json = skills_json
        if ats_score is not None:
            version.ats_score = ats_score
        if recommendations_json is not None:
            version.recommendations_json = recommendations_json

        await self._session.flush()
        return await self.get_by_id(version_id)

    async def delete(self, version_id: UUID) -> bool:
        version = await self.get_by_id(version_id)
        if version is None:
            return False
        await self._session.delete(version)
        await self._session.flush()
        return True

    async def get_by_id(self, version_id: UUID) -> ResumeTailoringVersion | None:
        result = await self._session.execute(
            select(ResumeTailoringVersion)
            .options(
                selectinload(ResumeTailoringVersion.resume),
                selectinload(ResumeTailoringVersion.tailoring_session),
            )
            .where(ResumeTailoringVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def list_by_resume(self, resume_id: UUID) -> list[ResumeTailoringVersion]:
        result = await self._session.execute(
            select(ResumeTailoringVersion)
            .where(ResumeTailoringVersion.resume_id == resume_id)
            .order_by(
                ResumeTailoringVersion.created_at.desc(),
                ResumeTailoringVersion.updated_at.desc(),
                ResumeTailoringVersion.id.desc(),
            )
        )
        return list(result.scalars().all())

    async def list_by_session(
        self, tailoring_session_id: UUID
    ) -> list[ResumeTailoringVersion]:
        result = await self._session.execute(
            select(ResumeTailoringVersion).where(
                ResumeTailoringVersion.tailoring_session_id == tailoring_session_id
            )
        )
        return list(result.scalars().all())

    async def get_by_session(
        self, tailoring_session_id: UUID
    ) -> ResumeTailoringVersion | None:
        result = await self._session.execute(
            select(ResumeTailoringVersion)
            .options(selectinload(ResumeTailoringVersion.resume))
            .where(ResumeTailoringVersion.tailoring_session_id == tailoring_session_id)
            .limit(1)
        )
        return result.scalar_one_or_none()
