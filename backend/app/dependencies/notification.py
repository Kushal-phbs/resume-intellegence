"""FastAPI dependency providers for notifications."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependency import get_db_session
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService


def get_notification_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> NotificationRepository:
    """Create a notification repository bound to the request async session."""
    return NotificationRepository(db_session)


def get_notification_service(
    notification_repository: NotificationRepository = Depends(
        get_notification_repository
    ),
) -> NotificationService:
    """Create and return a NotificationService instance."""
    return NotificationService(notification_repository)
