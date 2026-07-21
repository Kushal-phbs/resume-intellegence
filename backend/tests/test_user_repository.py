from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository


def _build_repository() -> tuple[UserRepository, AsyncMock]:
    session = AsyncMock()
    session.add = MagicMock()
    return UserRepository(session), session


def test_create_user_persists_and_returns_user() -> None:
    repository, session = _build_repository()

    user = asyncio.run(
        repository.create_user(
            email="john@example.com",
            full_name="John Doe",
            hashed_password="hashed-password",
            role=UserRole.USER.value,
        )
    )

    assert isinstance(user, User)
    assert user.email == "john@example.com"
    assert user.full_name == "John Doe"
    assert user.hashed_password == "hashed-password"
    assert user.role == UserRole.USER.value

    session.add.assert_called_once_with(user)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(user)


def test_get_by_email_returns_user_when_found() -> None:
    repository, session = _build_repository()
    expected = SimpleNamespace(email="john@example.com")
    result = MagicMock()
    result.scalar_one_or_none.return_value = expected
    session.execute = AsyncMock(return_value=result)

    found = asyncio.run(repository.get_by_email("john@example.com"))

    assert found is expected
    session.execute.assert_awaited_once()


def test_get_by_id_returns_user_when_found() -> None:
    repository, session = _build_repository()
    expected = SimpleNamespace(id=uuid4())
    result = MagicMock()
    result.scalar_one_or_none.return_value = expected
    session.execute = AsyncMock(return_value=result)

    found = asyncio.run(repository.get_by_id(expected.id))

    assert found is expected
    session.execute.assert_awaited_once()


def test_email_exists_returns_true_when_email_is_found() -> None:
    repository, _ = _build_repository()
    repository.get_by_email = AsyncMock(return_value=SimpleNamespace())

    exists = asyncio.run(repository.email_exists("john@example.com"))

    assert exists is True
    repository.get_by_email.assert_awaited_once_with("john@example.com")


def test_email_exists_returns_false_when_email_is_missing() -> None:
    repository, _ = _build_repository()
    repository.get_by_email = AsyncMock(return_value=None)

    exists = asyncio.run(repository.email_exists("john@example.com"))

    assert exists is False
    repository.get_by_email.assert_awaited_once_with("john@example.com")
