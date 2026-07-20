from unittest.mock import patch

import pytest

from app.llm.config import LLMConfig
from app.llm.factory import LLMFactory


class DummyGroqProvider:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config


def test_create_provider_returns_groq_provider() -> None:
    """Validate that the factory returns the correct provider for supported names."""
    config = LLMConfig(provider="GROQ", api_key="test-key", model="test-model")

    with patch("app.llm.factory.GroqProvider", DummyGroqProvider):
        provider = LLMFactory.create_provider(config)

    assert isinstance(provider, DummyGroqProvider)
    assert provider.config.provider == "GROQ"
    assert provider.config.api_key == "test-key"
    assert provider.config.model == "test-model"


def test_create_provider_unsupported_raises_value_error() -> None:
    """Validate the factory rejects unknown providers with a clear error."""
    config = LLMConfig(provider="unsupported", api_key="key", model="model")

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        LLMFactory.create_provider(config)
