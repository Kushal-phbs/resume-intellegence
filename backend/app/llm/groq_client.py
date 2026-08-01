"""Reusable async HTTP client for Groq chat completion API."""

from __future__ import annotations

import asyncio
from time import monotonic
from typing import Any

import httpx

from app.core.exceptions import ExternalServiceException
from app.core.logging import logger

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"


class GroqClient:
    """Async Groq API client with pooling, retries, and structured failures."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds
        self._max_retries = max(max_retries, 0)

        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout_seconds),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    async def chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Call Groq chat completions endpoint and return parsed JSON."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        started = monotonic()
        attempts = self._max_retries + 1

        for attempt in range(1, attempts + 1):
            try:
                response = await self._client.post(
                    "/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                )

                if (
                    response.status_code in _RETRYABLE_STATUS_CODES
                    and attempt < attempts
                ):
                    backoff = 0.5 * (2 ** (attempt - 1))
                    logger.warning(
                        "Groq request retryable status=%s attempt=%s/%s backoff=%.1fs",
                        response.status_code,
                        attempt,
                        attempts,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue

                response.raise_for_status()
                elapsed_ms = round((monotonic() - started) * 1000, 2)
                logger.info(
                    "Groq request success status=%s attempts=%s latency_ms=%.2f",
                    response.status_code,
                    attempt,
                    elapsed_ms,
                )
                return response.json()

            except httpx.TimeoutException as exc:
                if attempt < attempts:
                    backoff = 0.5 * (2 ** (attempt - 1))
                    logger.warning(
                        "Groq request timeout attempt=%s/%s backoff=%.1fs",
                        attempt,
                        attempts,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue

                elapsed_ms = round((monotonic() - started) * 1000, 2)
                logger.error(
                    "Groq request timeout exhausted attempts=%s latency_ms=%.2f",
                    attempt,
                    elapsed_ms,
                )
                raise ExternalServiceException(
                    "Groq API request timed out",
                    status_code=504,
                ) from exc

            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                if status_code in _RETRYABLE_STATUS_CODES and attempt < attempts:
                    backoff = 0.5 * (2 ** (attempt - 1))
                    logger.warning(
                        "Groq request retryable HTTP error status=%s attempt=%s/%s "
                        "backoff=%.1fs",
                        status_code,
                        attempt,
                        attempts,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue

                elapsed_ms = round((monotonic() - started) * 1000, 2)
                logger.error(
                    "Groq request failed status=%s attempts=%s latency_ms=%.2f",
                    status_code,
                    attempt,
                    elapsed_ms,
                )
                raise ExternalServiceException(
                    f"Groq API returned HTTP {status_code}",
                    status_code=502,
                ) from exc

            except httpx.RequestError as exc:
                if attempt < attempts:
                    backoff = 0.5 * (2 ** (attempt - 1))
                    logger.warning(
                        "Groq request transport error attempt=%s/%s backoff=%.1fs",
                        attempt,
                        attempts,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue

                elapsed_ms = round((monotonic() - started) * 1000, 2)
                logger.error(
                    "Groq request transport failure attempts=%s latency_ms=%.2f",
                    attempt,
                    elapsed_ms,
                )
                raise ExternalServiceException(
                    "Groq API request failed",
                    status_code=502,
                ) from exc

        # Unreachable because each branch returns or raises.
        raise ExternalServiceException("Groq API request failed", status_code=502)

    async def close(self) -> None:
        """Close the underlying HTTP client when owned by this instance."""
        if self._owns_client:
            await self._client.aclose()
