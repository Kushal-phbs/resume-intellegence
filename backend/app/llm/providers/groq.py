"""Groq LLM provider implementation."""

from __future__ import annotations

import asyncio
from time import monotonic

import httpx
from groq import APIConnectionError, APITimeoutError, AsyncGroq

from app.core.logging import logger
from app.llm.base import BaseLLMProvider
from app.llm.config import LLMConfig
from app.llm.models import LLMRequest, LLMResponse
from app.llm.response_parser import ResponseParser


class GroqProvider(BaseLLMProvider):
    """Provider implementation for Groq."""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        self._client = AsyncGroq(
            api_key=config.api_key,
            timeout=config.timeout,
            max_retries=0,
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response for the provided LLM request."""
        messages: list[dict[str, str]] = []

        if request.system_prompt is not None:
            messages.append(
                {
                    "role": "system",
                    "content": request.system_prompt,
                }
            )

        messages.append({"role": "user", "content": request.prompt})

        # Only retry safe transient network failures. Authentication, validation,
        # and other API errors should fail immediately because they are not
        # recoverable through additional retries.
        transient_errors = (
            APIConnectionError,
            APITimeoutError,
            httpx.ConnectError,
            httpx.ReadError,
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.TransportError,
        )

        logger.info(
            "LLM request started provider=%s model=%s",
            self._config.provider,
            self._config.model,
        )

        start_time = monotonic()
        last_error: Exception | None = None
        completion = None
        for attempt in range(1, max(self._config.max_retries, 1) + 1):
            try:
                completion = await self._client.chat.completions.create(
                    messages=messages,
                    model=self._config.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                )
                break
            except transient_errors as exc:
                last_error = exc
                if attempt >= self._config.max_retries:
                    latency_ms = (monotonic() - start_time) * 1000
                    logger.error(
                        "LLM request failed provider=%s model=%s status=failure "
                        "retry_count=%s latency_ms=%.1f",
                        self._config.provider,
                        self._config.model,
                        attempt - 1,
                        latency_ms,
                    )
                    raise

                backoff = 0.5 * (2 ** (attempt - 1))
                logger.warning(
                    "Transient Groq error on attempt %s/%s provider=%s model=%s, "
                    "retrying in %.1fs",
                    attempt,
                    self._config.max_retries,
                    self._config.provider,
                    self._config.model,
                    backoff,
                )
                await asyncio.sleep(backoff)
        else:
            assert last_error is not None
            raise last_error

        latency_ms = (monotonic() - start_time) * 1000
        retry_count = attempt - 1
        logger.info(
            "LLM request finished provider=%s model=%s status=success "
            "retry_count=%s latency_ms=%.1f",
            self._config.provider,
            self._config.model,
            retry_count,
            latency_ms,
        )

        choice = completion.choices[0]
        raw_content = choice.message.content or ""
        cleaned_content = ResponseParser.clean(raw_content)

        usage = completion.usage
        input_tokens = (
            getattr(usage, "prompt_tokens", None) if usage is not None else None
        )
        output_tokens = (
            getattr(usage, "completion_tokens", None) if usage is not None else None
        )
        total_tokens = (
            getattr(usage, "total_tokens", None) if usage is not None else None
        )
        latency_seconds = (
            getattr(usage, "total_time", None) if usage is not None else None
        ) or (getattr(usage, "completion_time", None) if usage is not None else None)
        latency_ms = latency_seconds * 1000 if latency_seconds is not None else None

        return LLMResponse(
            content=cleaned_content,
            model=completion.model,
            provider="groq",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            finish_reason=getattr(choice, "finish_reason", None),
        )
