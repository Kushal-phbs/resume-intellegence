"""FastAPI dependency providers for the job analysis domain."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependency import get_db_session
from app.dependencies.cache import get_cache_service
from app.dependencies.llm import get_llm_provider
from app.dependencies.resume import get_resume_repository, get_storage_provider
from app.llm.base import BaseLLMProvider
from app.repositories.job_analysis_repository import JobAnalysisRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.cache_service import CacheService
from app.services.chat_service import ChatService
from app.services.job_analysis_service import JobAnalysisService
from app.storage.base import StorageProvider


def get_job_analysis_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> JobAnalysisRepository:
    """Create a job analysis repository bound to the current async session."""
    return JobAnalysisRepository(db_session)


def get_job_description_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> JobDescriptionRepository:
    """Create a job description repository bound to the current async session."""
    return JobDescriptionRepository(db_session)


def get_chat_service(
    provider: BaseLLMProvider = Depends(get_llm_provider),
) -> ChatService:
    """Create a ChatService instance for job analysis workflows."""
    return ChatService(provider)


def get_job_analysis_service(
    job_analysis_repository: JobAnalysisRepository = Depends(
        get_job_analysis_repository
    ),
    resume_repository: ResumeRepository = Depends(get_resume_repository),
    job_description_repository: JobDescriptionRepository = Depends(
        get_job_description_repository
    ),
    storage_provider: StorageProvider = Depends(get_storage_provider),
    chat_service: ChatService = Depends(get_chat_service),
    cache_service: CacheService = Depends(get_cache_service),
) -> JobAnalysisService:
    """Create and return a JobAnalysisService instance."""
    return JobAnalysisService(
        job_analysis_repository,
        resume_repository,
        job_description_repository,
        storage_provider,
        chat_service,
        cache_service=cache_service,
    )
