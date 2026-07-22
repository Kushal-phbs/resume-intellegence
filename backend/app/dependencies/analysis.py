"""FastAPI dependency providers for the analysis domain."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependency import get_db_session
from app.dependencies.cache import get_cache_service
from app.dependencies.llm import get_llm_provider
from app.dependencies.resume import get_resume_repository, get_storage_provider
from app.llm.base import BaseLLMProvider
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.cache_service import CacheService
from app.services.chat_service import ChatService
from app.services.resume_analysis_service import ResumeAnalysisService
from app.storage.base import StorageProvider


def get_analysis_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> ResumeAnalysisRepository:
    """Create an analysis repository bound to the current async session."""
    return ResumeAnalysisRepository(db_session)


def get_chat_service(
    provider: BaseLLMProvider = Depends(get_llm_provider),
) -> ChatService:
    """Create a ChatService instance for analysis workflows."""
    return ChatService(provider)


def get_analysis_service(
    analysis_repository: ResumeAnalysisRepository = Depends(get_analysis_repository),
    resume_repository: ResumeRepository = Depends(get_resume_repository),
    storage_provider: StorageProvider = Depends(get_storage_provider),
    chat_service: ChatService = Depends(get_chat_service),
    cache_service: CacheService = Depends(get_cache_service),
) -> ResumeAnalysisService:
    """Create and return a ResumeAnalysisService instance."""
    return ResumeAnalysisService(
        analysis_repository,
        resume_repository,
        storage_provider,
        chat_service,
        cache_service=cache_service,
    )
