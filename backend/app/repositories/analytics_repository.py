"""Persistence operations for per-user analytics counters."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_analytics import UserAnalytics


class AnalyticsRepository:
    """Data-access operations for ``UserAnalytics`` rows."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        total_ai_requests: int = 0,
        total_tokens_used: int = 0,
        successful_requests: int = 0,
        failed_requests: int = 0,
        average_processing_time_ms: float | None = None,
        last_activity_at: datetime | None = None,
    ) -> UserAnalytics:
        analytics = UserAnalytics(
            user_id=user_id,
            total_ai_requests=total_ai_requests,
            total_tokens_used=total_tokens_used,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_processing_time_ms=average_processing_time_ms,
            last_activity_at=last_activity_at,
        )
        self._session.add(analytics)
        await self._session.flush()
        await self._session.refresh(analytics)
        return analytics

    async def update(
        self,
        analytics_id: UUID,
        *,
        total_ai_requests: int | None = None,
        total_tokens_used: int | None = None,
        successful_requests: int | None = None,
        failed_requests: int | None = None,
        average_processing_time_ms: float | None = None,
        last_activity_at: datetime | None = None,
    ) -> UserAnalytics | None:
        analytics = await self.get_by_id(analytics_id)
        if analytics is None:
            return None

        if total_ai_requests is not None:
            analytics.total_ai_requests = total_ai_requests
        if total_tokens_used is not None:
            analytics.total_tokens_used = total_tokens_used
        if successful_requests is not None:
            analytics.successful_requests = successful_requests
        if failed_requests is not None:
            analytics.failed_requests = failed_requests
        if average_processing_time_ms is not None:
            analytics.average_processing_time_ms = average_processing_time_ms
        if last_activity_at is not None:
            analytics.last_activity_at = last_activity_at

        await self._session.flush()
        return await self.get_by_id(analytics_id)

    async def delete(self, analytics_id: UUID) -> bool:
        analytics = await self.get_by_id(analytics_id)
        if analytics is None:
            return False
        await self._session.delete(analytics)
        await self._session.flush()
        return True

    async def get_by_id(self, analytics_id: UUID) -> UserAnalytics | None:
        result = await self._session.execute(
            select(UserAnalytics).where(UserAnalytics.id == analytics_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> UserAnalytics | None:
        result = await self._session.execute(
            select(UserAnalytics).where(UserAnalytics.user_id == user_id)
        )
        return result.scalar_one_or_none()
