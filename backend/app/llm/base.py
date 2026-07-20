"""Base interface for Large Language Model providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.llm.models import LLMRequest, LLMResponse


class BaseLLMProvider(ABC):
    """Abstract interface for all LLM providers."""

    @abstractmethod
    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """Generate a response from the language model.

        Args:
            request: The LLM request containing the prompt and generation options.

        Returns:
            A standardized LLM response.
        """
        ...
