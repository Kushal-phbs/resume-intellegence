import asyncio
from unittest.mock import AsyncMock

import pytest

from app.llm.models import LLMRequest, LLMResponse
from app.services.chat_service import ChatService


def test_chat_service_delegates_to_provider() -> None:
    """Verify ChatService forwards requests to the configured provider."""
    provider = AsyncMock()
    expected = LLMResponse(content="result", model="test-model", provider="groq")
    provider.generate.return_value = expected

    service = ChatService(provider)
    request = LLMRequest(prompt="hello")

    result = asyncio.run(service.chat(request))

    provider.generate.assert_awaited_once_with(request)
    assert result == expected


def test_chat_service_propagates_provider_error() -> None:
    """Verify ChatService does not swallow provider exceptions."""
    provider = AsyncMock()
    provider.generate.side_effect = RuntimeError("provider failure")

    service = ChatService(provider)
    request = LLMRequest(prompt="hello")

    with pytest.raises(RuntimeError, match="provider failure"):
        asyncio.run(service.chat(request))
