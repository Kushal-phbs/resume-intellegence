"""FastAPI dependency providers for dashboard and analytics domains."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependency import get_db_session
from app.dependencies.analysis import get_analysis_repository
from app.dependencies.cache import get_cache_service
from app.dependencies.job_analysis import get_job_analysis_repository
from app.dependencies.notification import get_notification_repository
from app.dependencies.resume import get_resume_repository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.job_analysis_repository import JobAnalysisRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository
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


def get_user_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    """Create a user repository bound to the request async session."""
    return UserRepository(db_session)


def get_dashboard_service(
    dashboard_repository: DashboardRepository = Depends(get_dashboard_repository),
    resume_repository: ResumeRepository = Depends(get_resume_repository),
    resume_analysis_repository: ResumeAnalysisRepository = Depends(
        get_analysis_repository
    ),
    job_analysis_repository: JobAnalysisRepository = Depends(
        get_job_analysis_repository
    ),
    notification_repository: NotificationRepository = Depends(
        get_notification_repository
    ),
    user_repository: UserRepository = Depends(get_user_repository),
    analytics_repository: AnalyticsRepository = Depends(get_analytics_repository),
    activity_repository: ActivityRepository = Depends(get_activity_repository),
    cache_service: CacheService = Depends(get_cache_service),
) -> DashboardService:
    """Create and return a DashboardService instance."""
    return DashboardService(
        dashboard_repository,
        analytics_repository,
        activity_repository,
        resume_repository,
        resume_analysis_repository,
        job_analysis_repository,
        notification_repository,
        user_repository,
        cache_service,
    )
