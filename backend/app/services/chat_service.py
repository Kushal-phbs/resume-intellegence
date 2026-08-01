"""Service layer for chat operations."""

from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from typing import Any, AsyncIterator
from uuid import UUID

from app.core.exceptions import ResourceNotFoundException
from app.core.logging import ai_processing_duration_ms_ctx, logger
from app.llm.models import LLMRequest, LLMResponse
from app.llm.providers.base_provider import BaseProvider
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.job_analysis_repository import JobAnalysisRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.chat import ConversationResponse, MessageResponse

_CHAT_SYSTEM_PROMPT = (
    "You are a resume intelligence assistant. Use the provided user context and "
    "conversation history to generate concise, actionable guidance."
)
_MAX_CONTEXT_MESSAGES = 15
_SUMMARY_TRIGGER_MESSAGES = 40
_STREAM_CHUNK_SIZE = 120

_SUMMARY_PROMPT = (
    "Summarize the prior conversation into concise bullet points with key facts, "
    "decisions, and unresolved questions. Keep it short and context-preserving."
)


def _estimate_tokens(text: str) -> int:
    """Estimate token count using a lightweight character heuristic."""
    if not text:
        return 0
    return max(1, len(text) // 4)


class ChatService:
    """Service that delegates chat requests to an LLM provider."""

    def __init__(
        self,
        *legacy_provider: BaseProvider,
        ai_provider: BaseProvider | None = None,
        conversation_repository: ConversationRepository | None = None,
        message_repository: MessageRepository | None = None,
        resume_repository: ResumeRepository | None = None,
        resume_analysis_repository: ResumeAnalysisRepository | None = None,
        job_analysis_repository: JobAnalysisRepository | None = None,
        dashboard_repository: DashboardRepository | None = None,
    ) -> None:
        if ai_provider is None and legacy_provider:
            ai_provider = legacy_provider[0]

        if ai_provider is None:
            raise RuntimeError("AI provider is not configured")

        self._ai_provider = ai_provider
        self._conversation_repository = conversation_repository
        self._message_repository = message_repository
        self._resume_repository = resume_repository
        self._resume_analysis_repository = resume_analysis_repository
        self._job_analysis_repository = job_analysis_repository
        self._dashboard_repository = dashboard_repository

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Bridge an LLM request to the configured provider."""
        started = perf_counter()

        # Backward-compatible bridge for tests and adapters that still expose
        # a `generate(LLMRequest)` method.
        if hasattr(self._ai_provider, "generate"):
            response = await self._ai_provider.generate(request)
        else:
            history: list[dict[str, str]] = []
            if request.system_prompt:
                history.append({"role": "system", "content": request.system_prompt})
            content, token_usage = await self._ai_provider.generate_reply(
                user_message=request.prompt,
                context={},
                history=history,
            )
            response = LLMResponse(
                content=content,
                provider="groq",
                input_tokens=int(token_usage.get("input_tokens", 0)),
                output_tokens=int(token_usage.get("output_tokens", 0)),
                total_tokens=int(token_usage.get("total_tokens", 0)),
            )

        elapsed_ms = round((perf_counter() - started) * 1000, 2)

        current = float(ai_processing_duration_ms_ctx.get("0.0"))
        ai_processing_duration_ms_ctx.set(str(round(current + elapsed_ms, 2)))
        logger.info("ai.request.completed")
        return response

    async def list_conversations(
        self,
        *,
        user_id: UUID,
        limit: int,
        offset: int,
    ) -> list[ConversationResponse]:
        """List all conversations owned by a user."""
        repository = self._require_conversation_repository()
        conversations = await repository.list_by_user(
            user_id,
            limit=limit,
            offset=offset,
        )
        return [ConversationResponse.model_validate(item) for item in conversations]

    async def create_conversation(
        self,
        *,
        user_id: UUID,
        title: str,
    ) -> ConversationResponse:
        """Create and return a new conversation for the user."""
        repository = self._require_conversation_repository()
        conversation = await repository.create(user_id=user_id, title=title)
        return ConversationResponse.model_validate(conversation)

    async def get_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> ConversationResponse:
        """Return one conversation when it belongs to the user."""
        conversation = await self._get_owned_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        return ConversationResponse.model_validate(conversation)

    async def rename_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        title: str,
    ) -> ConversationResponse:
        """Rename a user-owned conversation."""
        repository = self._require_conversation_repository()
        await self._get_owned_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        updated = await repository.rename(conversation_id, title=title)
        if updated is None:
            raise ResourceNotFoundException("Conversation not found")
        return ConversationResponse.model_validate(updated)

    async def delete_conversation(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
    ) -> None:
        """Delete a user-owned conversation."""
        repository = self._require_conversation_repository()
        await self._get_owned_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        deleted = await repository.delete(conversation_id)
        if not deleted:
            raise ResourceNotFoundException("Conversation not found")

    async def list_messages(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        limit: int,
        offset: int,
    ) -> list[MessageResponse]:
        """Return paginated messages for a user-owned conversation."""
        repository = self._require_message_repository()
        await self._get_owned_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        messages = await repository.list_messages(
            conversation_id,
            limit=limit,
            offset=offset,
        )
        return [MessageResponse.model_validate(item) for item in messages]

    async def send_message(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        content: str,
    ) -> tuple[
        ConversationResponse,
        MessageResponse,
        MessageResponse,
        dict[str, int],
        float,
    ]:
        """Persist user message, generate reply, and persist assistant message."""
        started = perf_counter()
        conversation = await self._get_owned_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        message_repository = self._require_message_repository()
        user_message = await message_repository.create(
            conversation_id=conversation_id,
            role="user",
            content=content,
            token_count=_estimate_tokens(content),
        )

        previous = await message_repository.list_messages(
            conversation_id,
            limit=1000,
            offset=0,
        )
        history = await self._build_provider_history(previous)
        context = await self._build_user_context(user_id)
        reply, token_usage = await self._ai_provider.generate_reply(
            user_message=content,
            context=context,
            history=history,
        )

        assistant_message = await message_repository.create(
            conversation_id=conversation_id,
            role="assistant",
            content=reply,
            token_count=int(token_usage.get("output_tokens", _estimate_tokens(reply))),
        )

        conversation.updated_at = datetime.now(UTC)
        elapsed = round(perf_counter() - started, 4)
        return (
            ConversationResponse.model_validate(conversation),
            MessageResponse.model_validate(user_message),
            MessageResponse.model_validate(assistant_message),
            {
                "input_tokens": int(token_usage.get("input_tokens", 0)),
                "output_tokens": int(token_usage.get("output_tokens", 0)),
                "total_tokens": int(token_usage.get("total_tokens", 0)),
            },
            elapsed,
        )

    async def stream_reply(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        content: str,
    ) -> AsyncIterator[str]:
        """Yield assistant response chunks without changing persisted messages."""
        await self._get_owned_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        message_repository = self._require_message_repository()
        previous = await message_repository.list_messages(
            conversation_id,
            limit=1000,
            offset=0,
        )

        history = await self._build_provider_history(previous)
        context = await self._build_user_context(user_id)

        if hasattr(self._ai_provider, "stream_reply"):
            async for chunk in self._ai_provider.stream_reply(
                user_message=content,
                context=context,
                history=history,
            ):
                yield chunk
            return

        reply, _ = await self._ai_provider.generate_reply(
            user_message=content,
            context=context,
            history=history,
        )
        for chunk in self._chunk_text(reply):
            yield chunk

    async def _build_provider_history(
        self,
        messages: list[Any],
    ) -> list[dict[str, str]]:
        """Build chronological provider history including a system instruction."""
        rolling_messages = messages[-_MAX_CONTEXT_MESSAGES:]
        history: list[dict[str, str]] = [
            {"role": "system", "content": _CHAT_SYSTEM_PROMPT}
        ]

        if len(messages) > _SUMMARY_TRIGGER_MESSAGES:
            summary = await self._summarize_messages(messages[:-_MAX_CONTEXT_MESSAGES])
            if summary:
                history.append(
                    {
                        "role": "system",
                        "content": f"Conversation summary: {summary}",
                    }
                )
                # TODO: Persist the summary on Conversation when a summary field exists.

        history.extend(
            {"role": item.role, "content": item.content} for item in rolling_messages
        )
        return history

    async def _summarize_messages(self, messages: list[Any]) -> str:
        """Generate a compact summary for older conversation turns."""
        if not messages:
            return ""

        summary_history = [
            {"role": item.role, "content": item.content}
            for item in messages
            if getattr(item, "content", None)
        ]
        if not summary_history:
            return ""

        try:
            summary, _ = await self._ai_provider.generate_reply(
                user_message=_SUMMARY_PROMPT,
                context={},
                history=summary_history,
            )
        except Exception:
            logger.warning("chat.summary.generation_failed")
            return ""

        return summary.strip()

    def _chunk_text(self, text: str) -> list[str]:
        if not text:
            return []
        return [
            text[i : i + _STREAM_CHUNK_SIZE]
            for i in range(0, len(text), _STREAM_CHUNK_SIZE)
        ]

    async def _build_user_context(self, user_id: UUID) -> dict[str, Any]:
        """Collect latest resume, analysis, job analysis, and dashboard metrics."""
        resume_repository = self._require_resume_repository()
        analysis_repository = self._require_resume_analysis_repository()
        job_repository = self._require_job_analysis_repository()
        dashboard_repository = self._require_dashboard_repository()

        resumes = await resume_repository.list_by_user(user_id)
        latest_resume = None
        latest_version = None
        latest_resume_analysis = None
        if resumes:
            latest_resume = max(resumes, key=lambda item: item.created_at)
            latest_version = await resume_repository.get_latest_version(
                latest_resume.id
            )
            latest_resume_analysis = await analysis_repository.get_latest_completed(
                latest_resume.id
            )
            if latest_resume_analysis is None:
                latest_resume_analysis = await analysis_repository.get_latest(
                    latest_resume.id
                )

        job_analyses = await job_repository.list_by_user(user_id)
        latest_job_analysis = job_analyses[0] if job_analyses else None
        dashboard = await dashboard_repository.calculate_metrics(user_id)

        return {
            "latest_resume": {
                "id": str(latest_resume.id),
                "title": latest_resume.title,
                "is_primary": latest_resume.is_primary,
            }
            if latest_resume
            else None,
            "latest_resume_version": {
                "id": str(latest_version.id),
                "version_number": latest_version.version_number,
            }
            if latest_version
            else None,
            "latest_resume_analysis": {
                "id": str(latest_resume_analysis.id),
                "resume_score": latest_resume_analysis.resume_score,
                "ats_score": latest_resume_analysis.ats_score,
                "strengths": latest_resume_analysis.strengths,
                "weaknesses": latest_resume_analysis.weaknesses,
            }
            if latest_resume_analysis
            else None,
            "latest_job_analysis": {
                "id": str(latest_job_analysis.id),
                "match_score": latest_job_analysis.match_score,
                "ats_match_score": latest_job_analysis.ats_match_score,
                "summary": latest_job_analysis.summary,
            }
            if latest_job_analysis
            else None,
            "dashboard": dashboard,
        }

    async def _get_owned_conversation(self, *, user_id: UUID, conversation_id: UUID):
        repository = self._require_conversation_repository()
        conversation = await repository.get(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise ResourceNotFoundException("Conversation not found")
        return conversation

    def _require_conversation_repository(self) -> ConversationRepository:
        if self._conversation_repository is None:
            raise RuntimeError("conversation_repository is not configured")
        return self._conversation_repository

    def _require_message_repository(self) -> MessageRepository:
        if self._message_repository is None:
            raise RuntimeError("message_repository is not configured")
        return self._message_repository

    def _require_resume_repository(self) -> ResumeRepository:
        if self._resume_repository is None:
            raise RuntimeError("resume_repository is not configured")
        return self._resume_repository

    def _require_resume_analysis_repository(self) -> ResumeAnalysisRepository:
        if self._resume_analysis_repository is None:
            raise RuntimeError("resume_analysis_repository is not configured")
        return self._resume_analysis_repository

    def _require_job_analysis_repository(self) -> JobAnalysisRepository:
        if self._job_analysis_repository is None:
            raise RuntimeError("job_analysis_repository is not configured")
        return self._job_analysis_repository

    def _require_dashboard_repository(self) -> DashboardRepository:
        if self._dashboard_repository is None:
            raise RuntimeError("dashboard_repository is not configured")
        return self._dashboard_repository
