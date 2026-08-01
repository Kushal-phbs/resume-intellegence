"""FastAPI dependency providers for resume tailoring and export domains."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependency import get_db_session
from app.dependencies.llm import get_llm_provider
from app.dependencies.notification import get_notification_service
from app.dependencies.resume import get_resume_repository, get_storage_provider
from app.llm.base import BaseLLMProvider
from app.repositories.cover_letter_repository import CoverLetterRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.resume_version_repository import ResumeVersionRepository
from app.repositories.tailoring_session_repository import TailoringSessionRepository
from app.services.chat_service import ChatService
from app.services.export_service import ExportService
from app.services.notification_service import NotificationService
from app.services.resume_tailoring_service import ResumeTailoringService
from app.storage.base import StorageProvider


def get_tailoring_session_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> TailoringSessionRepository:
    return TailoringSessionRepository(db_session)


def get_resume_version_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> ResumeVersionRepository:
    return ResumeVersionRepository(db_session)


def get_cover_letter_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> CoverLetterRepository:
    return CoverLetterRepository(db_session)


def get_job_description_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> JobDescriptionRepository:
    return JobDescriptionRepository(db_session)


def get_chat_service(
    provider: BaseLLMProvider = Depends(get_llm_provider),
) -> ChatService:
    return ChatService(provider)


def get_resume_tailoring_service(
    tailoring_session_repository: TailoringSessionRepository = Depends(
        get_tailoring_session_repository
    ),
    resume_version_repository: ResumeVersionRepository = Depends(
        get_resume_version_repository
    ),
    cover_letter_repository: CoverLetterRepository = Depends(
        get_cover_letter_repository
    ),
    resume_repository: ResumeRepository = Depends(get_resume_repository),
    job_description_repository: JobDescriptionRepository = Depends(
        get_job_description_repository
    ),
    storage_provider: StorageProvider = Depends(get_storage_provider),
    chat_service: ChatService = Depends(get_chat_service),
    notification_service: NotificationService = Depends(get_notification_service),
) -> ResumeTailoringService:
    return ResumeTailoringService(
        tailoring_session_repository,
        resume_version_repository,
        cover_letter_repository,
        resume_repository,
        job_description_repository,
        storage_provider,
        chat_service,
        notification_service,
    )


def get_export_service(
    resume_version_repository: ResumeVersionRepository = Depends(
        get_resume_version_repository
    ),
    cover_letter_repository: CoverLetterRepository = Depends(
        get_cover_letter_repository
    ),
    resume_repository: ResumeRepository = Depends(get_resume_repository),
    storage_provider: StorageProvider = Depends(get_storage_provider),
) -> ExportService:
    return ExportService(
        resume_version_repository,
        cover_letter_repository,
        resume_repository,
        storage_provider,
    )
