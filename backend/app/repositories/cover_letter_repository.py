"""Persistence operations for generated cover letters."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cover_letter import CoverLetter
from app.models.tailoring_session import TailoringSession


class CoverLetterRepository:
    """Data-access operations for cover letter records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tailoring_session_id: UUID,
        title: str,
        greeting: str,
        introduction: str,
        body: str,
        closing: str,
    ) -> CoverLetter:
        letter = CoverLetter(
            tailoring_session_id=tailoring_session_id,
            title=title,
            greeting=greeting,
            introduction=introduction,
            body=body,
            closing=closing,
        )
        self._session.add(letter)
        await self._session.flush()
        await self._session.refresh(letter)
        return letter

    async def update(
        self,
        cover_letter_id: UUID,
        *,
        title: str | None = None,
        greeting: str | None = None,
        introduction: str | None = None,
        body: str | None = None,
        closing: str | None = None,
    ) -> CoverLetter | None:
        letter = await self.get_by_id(cover_letter_id)
        if letter is None:
            return None

        if title is not None:
            letter.title = title
        if greeting is not None:
            letter.greeting = greeting
        if introduction is not None:
            letter.introduction = introduction
        if body is not None:
            letter.body = body
        if closing is not None:
            letter.closing = closing

        await self._session.flush()
        return await self.get_by_id(cover_letter_id)

    async def delete(self, cover_letter_id: UUID) -> bool:
        letter = await self.get_by_id(cover_letter_id)
        if letter is None:
            return False
        await self._session.delete(letter)
        await self._session.flush()
        return True

    async def get_by_id(self, cover_letter_id: UUID) -> CoverLetter | None:
        result = await self._session.execute(
            select(CoverLetter)
            .options(
                selectinload(CoverLetter.tailoring_session).selectinload(
                    TailoringSession.resume
                )
            )
            .where(CoverLetter.id == cover_letter_id)
        )
        return result.scalar_one_or_none()

    async def list_by_resume(self, resume_id: UUID) -> list[CoverLetter]:
        result = await self._session.execute(
            select(CoverLetter)
            .join(CoverLetter.tailoring_session)
            .where(TailoringSession.resume_id == resume_id)
            .order_by(
                CoverLetter.created_at.desc(),
                CoverLetter.updated_at.desc(),
                CoverLetter.id.desc(),
            )
        )
        return list(result.scalars().all())

    async def list_by_session(self, tailoring_session_id: UUID) -> list[CoverLetter]:
        result = await self._session.execute(
            select(CoverLetter).where(
                CoverLetter.tailoring_session_id == tailoring_session_id
            )
        )
        return list(result.scalars().all())

    async def get_by_session(self, tailoring_session_id: UUID) -> CoverLetter | None:
        result = await self._session.execute(
            select(CoverLetter)
            .options(
                selectinload(CoverLetter.tailoring_session).selectinload(
                    TailoringSession.resume
                )
            )
            .where(CoverLetter.tailoring_session_id == tailoring_session_id)
            .limit(1)
        )
        return result.scalar_one_or_none()
