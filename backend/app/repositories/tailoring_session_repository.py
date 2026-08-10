"""Persistence operations for tailoring sessions."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums.tailoring import TailoringStatus
from app.models.resume import Resume
from app.models.tailoring_session import TailoringSession


class TailoringSessionRepository:
    """Data-access operations for tailoring session records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        resume_id: UUID,
        job_description_id: UUID,
        status: TailoringStatus | str = TailoringStatus.PENDING,
    ) -> TailoringSession:
        session = TailoringSession(
            resume_id=resume_id,
            job_description_id=job_description_id,
            status=status.value if isinstance(status, TailoringStatus) else status,
        )
        self._session.add(session)
        await self._session.flush()
        await self._session.refresh(session)
        return session

    async def update(
        self,
        session_id: UUID,
        *,
        status: TailoringStatus | str | None = None,
    ) -> TailoringSession | None:
        session = await self.get_by_id(session_id)
        if session is None:
            return None

        if status is not None:
            session.status = (
                status.value if isinstance(status, TailoringStatus) else status
            )

        await self._session.flush()
        await self._session.refresh(session)
        return session

    async def delete(
        self,
        session_id: UUID,
        *,
        session: TailoringSession | None = None,
    ) -> bool:
        if session is None:
            session = await self.get_by_id(session_id)
        if session is None:
            return False
        await self._session.delete(session)
        await self._session.flush()
        return True

    async def get_by_id(self, session_id: UUID) -> TailoringSession | None:
        result = await self._session.execute(
            select(TailoringSession)
            .options(
                selectinload(TailoringSession.resume),
                selectinload(TailoringSession.job_description),
            )
            .where(TailoringSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_by_resume(self, resume_id: UUID) -> list[TailoringSession]:
        result = await self._session.execute(
            select(TailoringSession)
            .where(TailoringSession.resume_id == resume_id)
            .order_by(
                TailoringSession.created_at.desc(),
                TailoringSession.updated_at.desc(),
                TailoringSession.id.desc(),
            )
        )
        return list(result.scalars().all())

    async def list_by_user(self, user_id: UUID) -> list[TailoringSession]:
        result = await self._session.execute(
            select(TailoringSession)
            .join(TailoringSession.resume)
            .options(
                selectinload(TailoringSession.resume_version),
                selectinload(TailoringSession.cover_letter),
            )
            .where(Resume.user_id == user_id)
            .order_by(
                TailoringSession.created_at.desc(),
                TailoringSession.updated_at.desc(),
                TailoringSession.id.desc(),
            )
        )
        return list(result.scalars().all())

    async def list_by_session(self, session_id: UUID) -> list[TailoringSession]:
        session = await self.get_by_id(session_id)
        return [session] if session is not None else []
