from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.repositories.notification_repository import NotificationRepository


def _build_repository() -> tuple[NotificationRepository, AsyncMock]:
    session = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return NotificationRepository(session), session


def test_create_persists_and_returns_notification() -> None:
    repository, session = _build_repository()
    user_id = uuid4()

    notification = asyncio.run(
        repository.create(
            user_id=user_id,
            title="Title",
            message="Message",
            type="resume_uploaded",
            priority="medium",
        )
    )

    assert notification.user_id == user_id
    assert notification.type == "resume_uploaded"
    assert notification.is_read is False
    session.add.assert_called_once_with(notification)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(notification)


def test_get_by_id_returns_none_when_missing() -> None:
    repository, session = _build_repository()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)

    notification = asyncio.run(repository.get_by_id(uuid4()))

    assert notification is None


def test_list_unread_returns_items() -> None:
    repository, session = _build_repository()
    expected = [SimpleNamespace(id=uuid4()), SimpleNamespace(id=uuid4())]
    result = MagicMock()
    result.scalars.return_value.all.return_value = expected
    session.execute = AsyncMock(return_value=result)

    items = asyncio.run(repository.list_unread(uuid4(), limit=10))

    assert items == expected


def test_mark_all_as_read_updates_all_unread_rows() -> None:
    repository, session = _build_repository()
    unread = [SimpleNamespace(is_read=False), SimpleNamespace(is_read=False)]
    repository.list_unread = AsyncMock(return_value=unread)

    count = asyncio.run(repository.mark_all_as_read(uuid4()))

    assert count == 2
    assert all(item.is_read for item in unread)
    session.flush.assert_awaited_once()


def test_count_unread_returns_int_count() -> None:
    repository, session = _build_repository()
    result = MagicMock()
    result.scalar_one.return_value = 3
    session.execute = AsyncMock(return_value=result)

    count = asyncio.run(repository.count_unread(uuid4()))

    assert count == 3


def test_paginate_returns_items_and_total() -> None:
    repository, _session = _build_repository()
    expected_items = [SimpleNamespace(id=uuid4())]
    repository.list_for_user = AsyncMock(return_value=expected_items)

    result = MagicMock()
    result.scalar_one.return_value = 11
    repository._session.execute = AsyncMock(return_value=result)

    items, total = asyncio.run(
        repository.paginate(
            uuid4(),
            only_unread=True,
            priority="high",
            order="asc",
            limit=5,
            offset=10,
        )
    )

    assert items == expected_items
    assert total == 11
