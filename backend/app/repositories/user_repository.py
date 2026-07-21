"""Persistence operations for User entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Data-access operations for users.

    This repository is intentionally persistence-only and contains no business
    rules, password hashing, or token logic.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Return a user by email or None when not found."""
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Return a user by UUID or None when not found."""
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        *,
        email: str,
        full_name: str,
        hashed_password: str,
        role: str,
        is_active: bool = True,
    ) -> User:
        """Create and persist a user row, returning the ORM entity."""
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            is_active=is_active,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def email_exists(self, email: str) -> bool:
        """Return True when a user with the given email exists."""
        user = await self.get_by_email(email)
        return user is not None
