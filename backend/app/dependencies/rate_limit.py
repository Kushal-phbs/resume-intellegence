"""Reusable dependency for endpoint-level rate limiting."""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable

from fastapi import Depends, Request, Response

from app.config import settings
from app.core.exceptions import RateLimitException
from app.dependencies.cache import get_rate_limiter_service
from app.services.rate_limiter_service import RateLimiterService


def limit(
    *,
    bucket: str,
    requests: int,
    window_seconds: int | None = None,
) -> Callable[..., Awaitable[None]]:
    """Create a dependency that enforces a fixed-window rate limit."""

    async def _dependency(
        request: Request,
        response: Response,
        limiter: RateLimiterService = Depends(get_rate_limiter_service),
    ) -> None:
        if not settings.rate_limit_enabled:
            return

        client_ip = request.client.host if request.client else "unknown"
        user_identifier = str(getattr(request.state, "user_id", "anonymous"))
        raw_identifier = (
            f"{client_ip}|{user_identifier}|{request.method}|{request.url.path}"
        )
        identifier = hashlib.sha256(raw_identifier.encode("utf-8")).hexdigest()

        decision = await limiter.check(
            bucket=bucket,
            identifier=identifier,
            limit=requests,
            window_seconds=window_seconds or settings.rate_limit_window_seconds,
        )

        response.headers["X-RateLimit-Limit"] = str(requests)
        response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
        response.headers["X-RateLimit-Reset"] = str(decision.retry_after_seconds)

        if not decision.allowed:
            response.headers["Retry-After"] = str(decision.retry_after_seconds)
            raise RateLimitException(retry_after_seconds=decision.retry_after_seconds)

    return _dependency
