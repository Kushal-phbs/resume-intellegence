from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.repositories.conversation_repository import ConversationRepository


def _build_repository() -> tuple[ConversationRepository, AsyncMock]:
    session = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return ConversationRepository(session), session


def test_create_persists_and_returns_conversation() -> None:
    repository, session = _build_repository()
    user_id = uuid4()

    conversation = asyncio.run(
        repository.create(user_id=user_id, title="Interview Session")
    )

    assert conversation.user_id == user_id
    assert conversation.title == "Interview Session"
    session.add.assert_called_once_with(conversation)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(conversation)


def test_list_by_user_returns_rows() -> None:
    repository, session = _build_repository()
    expected = [SimpleNamespace(id=uuid4()), SimpleNamespace(id=uuid4())]
    result = MagicMock()
    result.scalars.return_value.all.return_value = expected
    session.execute = AsyncMock(return_value=result)

    rows = asyncio.run(repository.list_by_user(uuid4()))

    assert rows == expected


def test_rename_updates_title() -> None:
    repository, _session = _build_repository()
    item = SimpleNamespace(
        id=uuid4(),
        title="Old",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repository.get = AsyncMock(return_value=item)

    updated = asyncio.run(repository.rename(item.id, title="New"))

    assert updated is item
    assert item.title == "New"


def test_delete_returns_false_when_missing() -> None:
    repository, session = _build_repository()
    repository.get = AsyncMock(return_value=None)

    deleted = asyncio.run(repository.delete(uuid4()))

    assert deleted is False
    session.delete.assert_not_awaited()
