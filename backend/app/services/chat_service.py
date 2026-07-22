"""Service layer for chat operations."""

from __future__ import annotations

from time import perf_counter

from app.core.logging import ai_processing_duration_ms_ctx, logger
from app.llm.base import BaseLLMProvider
from app.llm.models import LLMRequest, LLMResponse


class ChatService:
    """Service that delegates chat requests to an LLM provider."""

    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self._provider = llm_provider

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Bridge an LLM request to the configured provider."""
        started = perf_counter()
        response = await self._provider.generate(request)
        elapsed_ms = round((perf_counter() - started) * 1000, 2)

        current = float(ai_processing_duration_ms_ctx.get("0.0"))
        ai_processing_duration_ms_ctx.set(str(round(current + elapsed_ms, 2)))
        logger.info("ai.request.completed")
        return response
