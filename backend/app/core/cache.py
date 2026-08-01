"""Reusable async Redis cache wrapper with graceful in-memory fallback."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config.settings import settings
from app.core.logging import logger


class RedisCache:
    """Provide key-based async cache operations backed by Redis."""

    def __init__(
        self,
        *,
        redis_url: str | None = None,
        default_ttl_seconds: int = 300,
        enabled: bool | None = None,
    ) -> None:
        self._enabled = settings.redis_enabled if enabled is None else enabled
        self._redis_url = redis_url or settings.redis_url
        self._default_ttl_seconds = max(int(default_ttl_seconds), 1)

        self._redis: Redis | None = None
        self._fallback_store: dict[str, tuple[datetime, str]] = {}
        self._redis_backoff_until: datetime | None = None

    async def get(self, key: str) -> Any | None:
        payload = await self._redis_get(key)
        if payload is None:
            payload = self._fallback_get_raw(key)
            if payload is None:
                return None

        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            logger.warning("cache.payload.decode_failed key=%s", key)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        ttl = max(ttl_seconds or self._default_ttl_seconds, 1)
        payload = json.dumps(value, default=str)

        if not await self._redis_set(key, payload, ttl):
            self._fallback_set_raw(key, payload, ttl)

    async def delete(self, key: str) -> None:
        await self._redis_delete(key)
        self._fallback_store.pop(key, None)

    async def delete_pattern(self, pattern: str) -> None:
        await self._redis_delete_pattern(pattern)

        keys_to_delete = [
            key for key in self._fallback_store if self._matches_pattern(key, pattern)
        ]
        for key in keys_to_delete:
            self._fallback_store.pop(key, None)

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
        self._redis_backoff_until = None

    async def _get_redis(self) -> Redis | None:
        if not self._enabled:
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
            except RedisError:
                logger.warning("cache.redis.initialization_failed", exc_info=True)
                self._redis = None
                self._set_redis_backoff()

        return self._redis

    async def _redis_get(self, key: str) -> str | None:
        redis = await self._get_redis()
        if redis is None:
            return None

        try:
            payload = await redis.get(key)
            if payload is not None:
                return str(payload)
        except RedisError:
            logger.warning("cache.redis.get_failed key=%s", key, exc_info=True)
            self._set_redis_backoff()
        return None

    async def _redis_set(self, key: str, payload: str, ttl_seconds: int) -> bool:
        redis = await self._get_redis()
        if redis is None:
            return False

        try:
            await redis.set(key, payload, ex=ttl_seconds)
            return True
        except RedisError:
            logger.warning("cache.redis.set_failed key=%s", key, exc_info=True)
            self._set_redis_backoff()
            return False

    async def _redis_delete(self, key: str) -> None:
        redis = await self._get_redis()
        if redis is None:
            return

        try:
            await redis.delete(key)
        except RedisError:
            logger.warning("cache.redis.delete_failed key=%s", key, exc_info=True)
            self._set_redis_backoff()

    async def _redis_delete_pattern(self, pattern: str) -> None:
        redis = await self._get_redis()
        if redis is None:
            return

        try:
            keys = [key async for key in redis.scan_iter(match=pattern)]
            if keys:
                await redis.delete(*keys)
        except RedisError:
            logger.warning(
                "cache.redis.delete_pattern_failed pattern=%s",
                pattern,
                exc_info=True,
            )
            self._set_redis_backoff()

    def _set_redis_backoff(self) -> None:
        self._redis = None
        self._redis_backoff_until = datetime.now(UTC) + timedelta(seconds=30)

    def _fallback_get_raw(self, key: str) -> str | None:
        record = self._fallback_store.get(key)
        if record is None:
            return None

        expires_at, payload = record
        now = datetime.now(UTC)
        if now >= expires_at:
            self._fallback_store.pop(key, None)
            return None

        return payload

    def _fallback_set_raw(self, key: str, payload: str, ttl_seconds: int) -> None:
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        self._fallback_store[key] = (expires_at, payload)

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            return key.startswith(pattern[:-1])
        return key == pattern
