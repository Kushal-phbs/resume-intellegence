"""FastAPI dependency providers for chat assistant module."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.db.dependency import get_db_session
from app.dependencies.analysis import get_analysis_repository
from app.dependencies.dashboard import get_dashboard_repository
from app.dependencies.job_analysis import get_job_analysis_repository
from app.dependencies.resume import get_resume_repository
from app.llm.groq_client import GroqClient
from app.llm.providers.base_provider import BaseProvider
from app.llm.providers.groq_provider import GroqProvider
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.job_analysis_repository import JobAnalysisRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.chat_service import ChatService


def get_conversation_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> ConversationRepository:
    """Create conversation repository bound to request session."""
    return ConversationRepository(db_session)


def get_message_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> MessageRepository:
    """Create message repository bound to request session."""
    return MessageRepository(db_session)


def get_groq_client() -> GroqClient:
    """Create Groq HTTP client for the current dependency resolution."""
    return GroqClient(
        api_key=settings.groq_api_key,
        base_url=settings.groq_base_url,
        timeout_seconds=float(settings.groq_http_timeout),
        max_retries=settings.groq_max_retries,
    )


def get_groq_provider(
    groq_client: GroqClient = Depends(get_groq_client),
) -> BaseProvider:
    """Create Groq-backed AI provider for chat generation."""
    return GroqProvider(client=groq_client)


def get_chat_service(
    groq_provider: BaseProvider = Depends(get_groq_provider),
    conversation_repository: ConversationRepository = Depends(
        get_conversation_repository
    ),
    message_repository: MessageRepository = Depends(get_message_repository),
    resume_repository: ResumeRepository = Depends(get_resume_repository),
    resume_analysis_repository: ResumeAnalysisRepository = Depends(
        get_analysis_repository
    ),
    job_analysis_repository: JobAnalysisRepository = Depends(
        get_job_analysis_repository
    ),
    dashboard_repository: DashboardRepository = Depends(get_dashboard_repository),
) -> ChatService:
    """Create and return chat service ready for conversation workflows."""
    return ChatService(
        ai_provider=groq_provider,
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        resume_repository=resume_repository,
        resume_analysis_repository=resume_analysis_repository,
        job_analysis_repository=job_analysis_repository,
        dashboard_repository=dashboard_repository,
    )
