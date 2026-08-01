"""Persistence operations for activity logs."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.analytics import ActivityType, EntityType
from app.models.activity_log import ActivityLog


class ActivityRepository:
    """Data-access operations for user activity logs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        activity_type: ActivityType | str,
        entity_type: EntityType | str,
        entity_id: UUID | None,
        metadata_json: dict[str, object] | None = None,
    ) -> ActivityLog:
        """Insert and return a new activity log row."""
        activity = ActivityLog(
            user_id=user_id,
            activity_type=(
                activity_type.value
                if isinstance(activity_type, ActivityType)
                else activity_type
            ),
            entity_type=(
                entity_type.value
                if isinstance(entity_type, EntityType)
                else entity_type
            ),
            entity_id=entity_id,
            metadata_json=metadata_json or {},
        )
        self._session.add(activity)
        await self._session.flush()
        await self._session.refresh(activity)
        return activity

    async def record_activity(
        self,
        *,
        user_id: UUID,
        activity_type: ActivityType | str,
        entity_type: EntityType | str,
        entity_id: UUID | None,
        metadata_json: dict[str, object] | None = None,
    ) -> ActivityLog:
        """Backward-compatible alias for :meth:`create`."""
        return await self.create(
            user_id=user_id,
            activity_type=activity_type,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata_json,
        )

    async def update(
        self,
        activity_id: UUID,
        *,
        metadata_json: dict[str, object] | None = None,
    ) -> ActivityLog | None:
        """Update mutable activity fields and return refreshed row when found."""
        activity = await self.get_by_id(activity_id)
        if activity is None:
            return None

        if metadata_json is not None:
            activity.metadata_json = metadata_json

        await self._session.flush()
        return await self.get_by_id(activity_id)

    async def delete(self, activity_id: UUID) -> bool:
        """Delete an activity log by id."""
        activity = await self.get_by_id(activity_id)
        if activity is None:
            return False
        await self._session.delete(activity)
        await self._session.flush()
        return True

    async def get_by_id(self, activity_id: UUID) -> ActivityLog | None:
        """Return an activity log by id when present."""
        result = await self._session.execute(
            select(ActivityLog).where(ActivityLog.id == activity_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> list[ActivityLog]:
        """Return all activity logs for a user, newest first."""
        result = await self._session.execute(
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id)
            .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
        )
        return list(result.scalars().all())

    async def list_recent_activity(
        self,
        user_id: UUID,
        *,
        limit: int = 20,
    ) -> list[ActivityLog]:
        """Return recent activity logs for a user, newest first."""
        result = await self._session.execute(
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id)
            .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
