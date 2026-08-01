"""Persistence operations for notifications."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    """Data-access operations for user notifications."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        title: str,
        message: str,
        type: str,
        priority: str = "medium",
        action_url: str | None = None,
        metadata_json: dict[str, object] | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            priority=priority,
            is_read=False,
            action_url=action_url,
            metadata_json=metadata_json or {},
        )
        self._session.add(notification)
        await self._session.flush()
        await self._session.refresh(notification)
        return notification

    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        result = await self._session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        only_unread: bool = False,
        priority: str | None = None,
        order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        statement = select(Notification).where(Notification.user_id == user_id)
        if only_unread:
            statement = statement.where(Notification.is_read.is_(False))
        if priority is not None:
            statement = statement.where(Notification.priority == priority)

        if order == "asc":
            statement = statement.order_by(
                Notification.created_at.asc(),
                Notification.id.asc(),
            )
        else:
            statement = statement.order_by(
                Notification.created_at.desc(),
                Notification.id.desc(),
            )

        statement = statement.offset(offset).limit(limit)
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def list_unread(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
    ) -> list[Notification]:
        result = await self._session.execute(
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_as_read(self, notification_id: UUID) -> Notification | None:
        notification = await self.get_by_id(notification_id)
        if notification is None:
            return None
        if not notification.is_read:
            notification.is_read = True
            await self._session.flush()
        return notification

    async def mark_all_as_read(self, user_id: UUID) -> int:
        notifications = await self.list_unread(user_id, limit=10_000)
        if not notifications:
            return 0

        for notification in notifications:
            notification.is_read = True
        await self._session.flush()
        return len(notifications)

    async def delete(self, notification_id: UUID) -> bool:
        notification = await self.get_by_id(notification_id)
        if notification is None:
            return False
        await self._session.delete(notification)
        await self._session.flush()
        return True

    async def count_unread(self, user_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return int(result.scalar_one() or 0)

    async def paginate(
        self,
        user_id: UUID,
        *,
        only_unread: bool = False,
        priority: str | None = None,
        order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        filters = [Notification.user_id == user_id]
        if only_unread:
            filters.append(Notification.is_read.is_(False))
        if priority is not None:
            filters.append(Notification.priority == priority)

        count_result = await self._session.execute(
            select(func.count(Notification.id)).where(*filters)
        )
        total = int(count_result.scalar_one() or 0)

        items = await self.list_for_user(
            user_id,
            only_unread=only_unread,
            priority=priority,
            order=order,
            limit=limit,
            offset=offset,
        )
        return items, total
