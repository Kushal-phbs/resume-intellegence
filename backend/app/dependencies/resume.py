"""FastAPI dependency providers for the resume domain."""

from __future__ import annotations

from pathlib import Path

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.db.dependency import get_db_session
from app.dependencies.notification import get_notification_service
from app.repositories.resume_repository import ResumeRepository
from app.services.notification_service import NotificationService
from app.services.resume_service import ResumeService
from app.storage.base import StorageProvider
from app.storage.local import LocalStorageProvider

__all__ = [
    "get_storage_provider",
    "get_resume_repository",
    "get_resume_service",
]


def get_storage_provider() -> StorageProvider:
    """Create and return the configured storage provider."""
    return LocalStorageProvider(base_directory=Path(settings.resume_upload_dir))


def get_resume_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> ResumeRepository:
    """Create a resume repository bound to the request's async session."""
    return ResumeRepository(db_session)


def get_resume_service(
    resume_repository: ResumeRepository = Depends(get_resume_repository),
    storage_provider: StorageProvider = Depends(get_storage_provider),
    notification_service: NotificationService = Depends(get_notification_service),
) -> ResumeService:
    """Create and return a ``ResumeService`` instance."""
    return ResumeService(resume_repository, storage_provider, notification_service)
