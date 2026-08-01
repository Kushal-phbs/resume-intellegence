"""Business logic orchestration for notifications."""

from __future__ import annotations

from uuid import UUID

from app.core.exceptions import ResourceNotFoundException
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    NotificationCreate,
    NotificationListResponse,
    NotificationResponse,
)


class NotificationService:
    """Coordinates notification workflows."""

    def __init__(self, notification_repository: NotificationRepository) -> None:
        self._notifications = notification_repository

    async def create_notification(
        self,
        *,
        user_id: UUID,
        payload: NotificationCreate,
    ) -> NotificationResponse:
        notification = await self._notifications.create(
            user_id=user_id,
            title=payload.title,
            message=payload.message,
            type=payload.type,
            priority=payload.priority,
            action_url=payload.action_url,
            metadata_json=payload.metadata_json,
        )
        return NotificationResponse.model_validate(notification)

    async def get_notifications(
        self,
        *,
        user_id: UUID,
        limit: int,
        offset: int,
        order: str,
        only_unread: bool = False,
        priority: str | None = None,
    ) -> NotificationListResponse:
        items, total = await self._notifications.paginate(
            user_id,
            only_unread=only_unread,
            priority=priority,
            order=order,
            limit=limit,
            offset=offset,
        )
        return NotificationListResponse(
            items=[NotificationResponse.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def mark_read(
        self,
        *,
        user_id: UUID,
        notification_id: UUID,
    ) -> NotificationResponse:
        notification = await self._notifications.get_by_id(notification_id)
        if notification is None or notification.user_id != user_id:
            raise ResourceNotFoundException("Notification not found")

        updated = await self._notifications.mark_as_read(notification_id)
        if updated is None:
            raise ResourceNotFoundException("Notification not found")
        return NotificationResponse.model_validate(updated)

    async def mark_all_read(self, *, user_id: UUID) -> int:
        return await self._notifications.mark_all_as_read(user_id)

    async def delete_notification(
        self,
        *,
        user_id: UUID,
        notification_id: UUID,
    ) -> None:
        notification = await self._notifications.get_by_id(notification_id)
        if notification is None or notification.user_id != user_id:
            raise ResourceNotFoundException("Notification not found")

        deleted = await self._notifications.delete(notification_id)
        if not deleted:
            raise ResourceNotFoundException("Notification not found")

    async def count_unread(self, *, user_id: UUID) -> int:
        return await self._notifications.count_unread(user_id)
