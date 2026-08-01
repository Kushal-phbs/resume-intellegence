"""Configurable fixed-window rate limiter service."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after_seconds: int


class RateLimiterService:
    """Evaluate fixed-window request limits with Redis + local fallback."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._redis: Redis | None = None
        self._fallback: dict[str, tuple[int, datetime]] = {}
        self._redis_backoff_until: datetime | None = None

    async def check(
        self,
        *,
        bucket: str,
        identifier: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        safe_limit = max(limit, 1)
        safe_window = max(window_seconds, 1)
        key = f"rate_limit:{bucket}:{identifier}"

        redis_decision = await self._check_redis(
            key=key,
            limit=safe_limit,
            window_seconds=safe_window,
        )
        if redis_decision is not None:
            return redis_decision

        return self._check_fallback(
            key=key,
            limit=safe_limit,
            window_seconds=safe_window,
        )

    async def close(self) -> None:
        if self._redis is not None:
            try:
                await self._redis.aclose()
            except Exception:
                pass
            finally:
                self._redis = None
        self._redis_backoff_until = None

    async def _get_redis(self) -> Redis | None:
        if not settings.redis_enabled:
            return None

        if self._redis_backoff_until is not None:
            if datetime.now(UTC) < self._redis_backoff_until:
                return None
            self._redis_backoff_until = None

        if self._redis is None:
            try:
                self._redis = Redis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=0.2,
                    socket_timeout=0.2,
                )
            except (RedisError, RuntimeError, OSError):
                logger.warning(
                    "Rate limiter Redis initialization failed",
                    exc_info=True,
                )
                await self._set_redis_backoff()
        return self._redis

    async def _check_redis(
        self,
        *,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision | None:
        redis = await self._get_redis()
        if redis is None:
            return None

        try:
            current_count = int(await redis.incr(key))
            if current_count == 1:
                await redis.expire(key, window_seconds)

            ttl = int(await redis.ttl(key))
            retry_after = max(ttl, 1)

            if current_count > limit:
                return RateLimitDecision(
                    allowed=False,
                    remaining=0,
                    retry_after_seconds=retry_after,
                )

            return RateLimitDecision(
                allowed=True,
                remaining=max(limit - current_count, 0),
                retry_after_seconds=retry_after,
            )
        except (RedisError, RuntimeError, OSError):
            logger.warning("Rate limiter Redis check failed", exc_info=True)
            await self._set_redis_backoff()
            return None

    async def _set_redis_backoff(self) -> None:
        if self._redis is not None:
            try:
                await self._redis.aclose()
            except Exception:
                pass
            finally:
                self._redis = None
        self._redis_backoff_until = datetime.now(UTC) + timedelta(seconds=30)

    def _check_fallback(
        self,
        *,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=window_seconds)

        current = self._fallback.get(key)
        if current is None or now >= current[1]:
            self._fallback[key] = (1, expires_at)
            return RateLimitDecision(
                allowed=True,
                remaining=max(limit - 1, 0),
                retry_after_seconds=window_seconds,
            )

        count, expiry = current
        count += 1
        self._fallback[key] = (count, expiry)
        retry_after = max(math.ceil((expiry - now).total_seconds()), 1)

        if count > limit:
            return RateLimitDecision(
                allowed=False,
                remaining=0,
                retry_after_seconds=retry_after,
            )

        return RateLimitDecision(
            allowed=True,
            remaining=max(limit - count, 0),
            retry_after_seconds=retry_after,
        )
