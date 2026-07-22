"""Persistence operations for job descriptions."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_description import JobDescription


class JobDescriptionRepository:
    """Data-access operations for job description records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, job_description_id: UUID) -> JobDescription | None:
        """Return a job description by UUID."""
        result = await self._session.execute(
            select(JobDescription).where(JobDescription.id == job_description_id)
        )
        return result.scalar_one_or_none()
