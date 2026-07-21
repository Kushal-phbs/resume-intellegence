"""Persistence operations for Resume and ResumeVersion entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.models.resume_version import ResumeVersion


class ResumeRepository:
    """Data-access operations for resumes and their versions.

    This repository is intentionally persistence-only and contains no
    business rules or filesystem access.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, user_id: UUID, title: str, is_primary: bool = False
    ) -> Resume:
        """Create and persist a new resume row.

        Args:
            user_id: Owning user's primary key.
            title: Human-readable resume title.
            is_primary: Whether this resume should be marked primary.

        Returns:
            Persisted resume entity.
        """
        resume = Resume(user_id=user_id, title=title, is_primary=is_primary)
        self._session.add(resume)
        await self._session.flush()
        await self._session.refresh(resume)
        return resume

    async def get(self, resume_id: UUID) -> Resume | None:
        """Return a resume by UUID.

        Args:
            resume_id: Resume primary key.

        Returns:
            Matching resume entity or ``None`` when no row exists.
        """
        result = await self._session.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> list[Resume]:
        """Return all resumes owned by a user.

        Args:
            user_id: Owning user's primary key.

        Returns:
            List of resume entities, in no particular order.
        """
        result = await self._session.execute(
            select(Resume).where(Resume.user_id == user_id)
        )
        return list(result.scalars().all())

    async def delete(self, resume_id: UUID) -> bool:
        """Delete a resume by UUID.

        Args:
            resume_id: Resume primary key.

        Returns:
            ``True`` if a row was deleted, ``False`` if it did not exist.
        """
        resume = await self.get(resume_id)
        if resume is None:
            return False
        await self._session.delete(resume)
        await self._session.flush()
        return True

    async def create_version(
        self,
        *,
        resume_id: UUID,
        version_number: int,
        content: str,
        file_path: str | None,
    ) -> ResumeVersion:
        """Create and persist a new resume version row.

        Args:
            resume_id: Owning resume's primary key.
            version_number: Sequential version number for this resume.
            content: Extracted/plain-text content for this version.
            file_path: Storage key of the uploaded file, if any.

        Returns:
            Persisted resume version entity.
        """
        version = ResumeVersion(
            resume_id=resume_id,
            version_number=version_number,
            content=content,
            file_path=file_path,
        )
        self._session.add(version)
        await self._session.flush()
        await self._session.refresh(version)
        return version

    async def get_versions(self, resume_id: UUID) -> list[ResumeVersion]:
        """Return all versions of a resume, ordered by version number.

        Args:
            resume_id: Owning resume's primary key.

        Returns:
            List of resume version entities ordered ascending by version number.
        """
        result = await self._session.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number)
        )
        return list(result.scalars().all())

    async def get_latest_version(self, resume_id: UUID) -> ResumeVersion | None:
        """Return the most recent version of a resume, if any.

        Args:
            resume_id: Owning resume's primary key.

        Returns:
            Resume version entity with the highest version number, or
            ``None`` if the resume has no versions.
        """
        result = await self._session.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
