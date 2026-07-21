"""Persistence operations for User entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserRole
from app.models.user import User


class UserRepository:
    """Data-access operations for users.

    This repository is intentionally persistence-only and contains no business
    rules, password hashing, or token logic.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Return a user by email.

        Args:
            email: Unique user email.

        Returns:
            Matching user entity or ``None`` when no row exists.
        """
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Return a user by UUID.

        Args:
            user_id: User primary key.

        Returns:
            Matching user entity or ``None`` when no row exists.
        """
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        *,
        email: str,
        full_name: str,
        hashed_password: str,
        role: UserRole | str,
        is_active: bool = True,
    ) -> User:
        """Create and persist a user row.

        Args:
            email: User email.
            full_name: User display name.
            hashed_password: Pre-hashed password (hashing occurs in service layer).
            role: User role value.
            is_active: Account active state.

        Returns:
            Persisted user entity.
        """
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role.value if isinstance(role, UserRole) else role,
            is_active=is_active,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def email_exists(self, email: str) -> bool:
        """Return whether a user with the given email exists.

        Args:
            email: Unique user email.

        Returns:
            ``True`` if the email already exists, otherwise ``False``.
        """
        user = await self.get_by_email(email)
        return user is not None
