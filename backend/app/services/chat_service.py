"""Service layer for chat operations."""

from __future__ import annotations

from app.llm.base import BaseLLMProvider
from app.llm.models import LLMRequest, LLMResponse


class ChatService:
    """Service that delegates chat requests to an LLM provider."""

    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self._provider = llm_provider

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Bridge an LLM request to the configured provider."""
        return await self._provider.generate(request)
