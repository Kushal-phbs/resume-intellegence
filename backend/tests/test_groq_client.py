import asyncio

import httpx
import pytest

from app.core.exceptions import ExternalServiceException
from app.llm.groq_client import GroqClient


def test_chat_completion_sends_auth_and_returns_json() -> None:
    seen = {"auth": ""}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("Authorization", "")
        return httpx.Response(200, json={"id": "cmpl_1", "choices": []})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.groq.com/openai/v1",
    )
    groq = GroqClient(
        api_key="test-key",
        client=client,
        max_retries=0,
    )

    result = asyncio.run(
        groq.chat_completion(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Hello"}],
        )
    )

    assert seen["auth"] == "Bearer test-key"
    assert result["id"] == "cmpl_1"
    asyncio.run(client.aclose())


def test_chat_completion_retries_retryable_status() -> None:
    state = {"calls": 0}

    async def handler(_: httpx.Request) -> httpx.Response:
        state["calls"] += 1
        if state["calls"] == 1:
            return httpx.Response(429, json={"error": "rate_limited"})
        return httpx.Response(200, json={"ok": True})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.groq.com/openai/v1",
    )
    groq = GroqClient(api_key="test-key", client=client, max_retries=1)

    result = asyncio.run(
        groq.chat_completion(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Hello"}],
        )
    )

    assert state["calls"] == 2
    assert result["ok"] is True
    asyncio.run(client.aclose())


def test_chat_completion_raises_external_service_exception_on_timeout() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.groq.com/openai/v1",
    )
    groq = GroqClient(api_key="test-key", client=client, max_retries=0)

    with pytest.raises(ExternalServiceException, match="timed out"):
        asyncio.run(
            groq.chat_completion(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Hello"}],
            )
        )

    asyncio.run(client.aclose())


def test_close_closes_owned_client() -> None:
    groq = GroqClient(api_key="test-key", max_retries=0)

    asyncio.run(groq.close())

    assert groq._client.is_closed is True
