"""FastAPI dependency providers for dashboard and analytics domains."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependency import get_db_session
from app.dependencies.cache import get_cache_service
from app.repositories.activity_repository import ActivityRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.services.cache_service import CacheService
from app.services.dashboard_service import DashboardService


def get_dashboard_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> DashboardRepository:
    """Create a dashboard repository bound to the request async session."""
    return DashboardRepository(db_session)


def get_analytics_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> AnalyticsRepository:
    """Create an analytics repository bound to the request async session."""
    return AnalyticsRepository(db_session)


def get_activity_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> ActivityRepository:
    """Create an activity repository bound to the request async session."""
    return ActivityRepository(db_session)


def get_dashboard_service(
    dashboard_repository: DashboardRepository = Depends(get_dashboard_repository),
    analytics_repository: AnalyticsRepository = Depends(get_analytics_repository),
    activity_repository: ActivityRepository = Depends(get_activity_repository),
    cache_service: CacheService = Depends(get_cache_service),
) -> DashboardService:
    """Create and return a DashboardService instance."""
    return DashboardService(
        dashboard_repository,
        analytics_repository,
        activity_repository,
        cache_service,
    )
