from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import ResourceNotFoundException
from app.schemas.notification import NotificationCreate
from app.services.notification_service import NotificationService


def _build_service() -> tuple[NotificationService, AsyncMock]:
    repository = AsyncMock()
    return NotificationService(repository), repository


def _notification(user_id):
    return SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        title="Title",
        message="Message",
        type="resume_uploaded",
        priority="medium",
        is_read=False,
        action_url="/resumes/1",
        metadata_json={},
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )


def test_create_notification_returns_response() -> None:
    service, repository = _build_service()
    user_id = uuid4()
    repository.create.return_value = _notification(user_id)

    result = asyncio.run(
        service.create_notification(
            user_id=user_id,
            payload=NotificationCreate(
                title="Resume uploaded",
                message="Done",
                type="resume_uploaded",
            ),
        )
    )

    assert result.user_id == user_id
    repository.create.assert_awaited_once()


def test_get_notifications_returns_paginated_response() -> None:
    service, repository = _build_service()
    user_id = uuid4()
    repository.paginate.return_value = ([_notification(user_id)], 1)

    result = asyncio.run(
        service.get_notifications(
            user_id=user_id,
            limit=20,
            offset=0,
            order="desc",
            only_unread=False,
            priority=None,
        )
    )

    assert result.total == 1
    assert len(result.items) == 1


def test_mark_read_raises_when_not_found() -> None:
    service, repository = _build_service()
    repository.get_by_id.return_value = None

    with pytest.raises(ResourceNotFoundException):
        asyncio.run(service.mark_read(user_id=uuid4(), notification_id=uuid4()))


def test_mark_all_read_returns_count() -> None:
    service, repository = _build_service()
    repository.mark_all_as_read.return_value = 4

    count = asyncio.run(service.mark_all_read(user_id=uuid4()))

    assert count == 4


def test_delete_notification_raises_for_non_owner() -> None:
    service, repository = _build_service()
    repository.get_by_id.return_value = _notification(uuid4())

    with pytest.raises(ResourceNotFoundException):
        asyncio.run(
            service.delete_notification(user_id=uuid4(), notification_id=uuid4())
        )


def test_count_unread_returns_repository_value() -> None:
    service, repository = _build_service()
    repository.count_unread.return_value = 9

    count = asyncio.run(service.count_unread(user_id=uuid4()))

    assert count == 9
