"""Dependency providers for LLM functionality."""

from __future__ import annotations

from app.config.settings import settings
from app.llm.base import BaseLLMProvider
from app.llm.config import LLMConfig
from app.llm.factory import LLMFactory


def get_llm_provider() -> BaseLLMProvider:
    """Create and return an LLM provider using configured settings.

    The function reads provider configuration from the shared settings object
    and returns a fresh provider instance for each dependency resolution.
    """
    provider_name = getattr(settings, "llm_provider", None)
    api_key = getattr(settings, "groq_api_key", None)
    model = getattr(settings, "groq_model", None)

    if provider_name is None:
        raise AttributeError("settings.llm_provider must be defined")
    if api_key is None:
        raise AttributeError("settings.groq_api_key must be defined")
    if model is None:
        raise AttributeError("settings.groq_model must be defined")

    config = LLMConfig(
        provider=provider_name,
        api_key=api_key,
        model=model,
    )

    return LLMFactory.create_provider(config)
