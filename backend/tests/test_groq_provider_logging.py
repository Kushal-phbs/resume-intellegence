import asyncio
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from groq import AuthenticationError

from app.llm.config import LLMConfig
from app.llm.models import LLMRequest
from app.llm.providers.groq import GroqProvider


class DummyClient:
    def __init__(self, *args, **kwargs):
        self.chat = self
        self.completions = self
        self.create = AsyncMock()


def make_completion(content: str, model: str = "test-model") -> SimpleNamespace:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content), finish_reason="stop"
            )
        ],
        model=model,
        usage=SimpleNamespace(
            prompt_tokens=1, completion_tokens=2, total_tokens=3, total_time=0.05
        ),
    )


def test_groq_provider_logs_request_lifecycle(caplog: pytest.LogCaptureFixture) -> None:
    config = LLMConfig(provider="groq", api_key="test-key", model="test-model")
    completion = make_completion("hello")

    with patch(
        "app.llm.providers.groq.AsyncGroq", return_value=DummyClient()
    ) as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.create.return_value = completion

        provider = GroqProvider(config)
        request = LLMRequest(prompt="hello")

        caplog.set_level(logging.INFO)
        result = asyncio.run(provider.generate(request))

    assert result.content == "hello"
    assert mock_client.call_args.kwargs["timeout"] == 30.0
    assert mock_client.call_args.kwargs["max_retries"] == 0
    assert "LLM request started provider=groq model=test-model" in caplog.text
    assert (
        "LLM request finished provider=groq model=test-model status=success "
        "retry_count=0 latency_ms=" in caplog.text
    )


def test_groq_provider_logs_retry_count(caplog: pytest.LogCaptureFixture) -> None:
    config = LLMConfig(provider="groq", api_key="test-key", model="test-model")
    completion = make_completion("hello")
    dummy = DummyClient()
    dummy.create.side_effect = [httpx.ConnectError("transient"), completion]

    with patch("app.llm.providers.groq.AsyncGroq", return_value=dummy):
        provider = GroqProvider(config)
        request = LLMRequest(prompt="hello")

        caplog.set_level(logging.INFO)
        result = asyncio.run(provider.generate(request))

    assert result.content == "hello"
    assert "LLM request started provider=groq model=test-model" in caplog.text
    assert "retry_count=1" in caplog.text
    assert "status=success" in caplog.text
    assert (
        "Transient Groq error on attempt 1/2 provider=groq model=test-model"
        in caplog.text
    )


def test_groq_provider_does_not_retry_authentication_errors(
    caplog: pytest.LogCaptureFixture,
) -> None:
    config = LLMConfig(provider="groq", api_key="test-key", model="test-model")
    dummy = DummyClient()
    request = httpx.Request("GET", "https://api.groq.com")
    auth_error = AuthenticationError(
        "invalid api key",
        response=httpx.Response(401, request=request),
        body=None,
    )
    dummy.create.side_effect = auth_error

    with patch("app.llm.providers.groq.AsyncGroq", return_value=dummy):
        provider = GroqProvider(config)
        request = LLMRequest(prompt="hello")

        caplog.set_level(logging.INFO)
        with pytest.raises(AuthenticationError):
            asyncio.run(provider.generate(request))

    assert dummy.create.call_count == 1
    assert "Transient Groq error" not in caplog.text
    assert "status=failure" not in caplog.text
