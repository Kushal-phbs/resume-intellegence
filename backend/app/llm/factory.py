"""Factory for creating LLM provider instances.

The factory is provider-agnostic and constructs provider instances based on a
string name and explicit credentials passed in at call time.
"""

from __future__ import annotations

from app.llm.base import BaseLLMProvider
from app.llm.config import LLMConfig
from app.llm.providers.groq import GroqProvider


class LLMFactory:
    """Factory for creating language model provider instances."""

    @staticmethod
    def create_provider(config: LLMConfig) -> BaseLLMProvider:
        """Create an LLM provider instance from an immutable config object.

        Args:
            config: Immutable configuration for the provider.

        Raises:
            ValueError: If the provider is not supported.
        """
        normalized_name = config.provider.strip().lower()

        if normalized_name == "groq":
            return GroqProvider(config)

        raise ValueError(
            f"Unsupported LLM provider '{config.provider}'. Supported providers: groq."
        )
