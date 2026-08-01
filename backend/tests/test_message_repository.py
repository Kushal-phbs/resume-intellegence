from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.repositories.message_repository import MessageRepository


def _build_repository() -> tuple[MessageRepository, AsyncMock]:
    session = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    return MessageRepository(session), session


def test_create_persists_message_with_non_negative_tokens() -> None:
    repository, session = _build_repository()

    message = asyncio.run(
        repository.create(
            conversation_id=uuid4(),
            role="user",
            content="hello",
            token_count=-5,
        )
    )

    assert message.role == "user"
    assert message.token_count == 0
    session.add.assert_called_once_with(message)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(message)


def test_list_messages_returns_rows() -> None:
    repository, session = _build_repository()
    expected = [SimpleNamespace(id=uuid4())]
    result = MagicMock()
    result.scalars.return_value.all.return_value = expected
    session.execute = AsyncMock(return_value=result)

    rows = asyncio.run(repository.list_messages(uuid4(), limit=20, offset=0))

    assert rows == expected


def test_bulk_create_persists_all_rows() -> None:
    repository, session = _build_repository()

    rows = asyncio.run(
        repository.bulk_create(
            conversation_id=uuid4(),
            messages=[
                {"role": "system", "content": "ctx", "token_count": 3},
                {"role": "user", "content": "ask", "token_count": 2},
            ],
        )
    )

    assert len(rows) == 2
    session.add_all.assert_called_once()
    assert session.refresh.await_count == 2
