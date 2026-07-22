"""Redis-backed cache service with graceful in-memory fallback."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Provide namespaced async caching operations.

    Redis is preferred for distributed cache consistency. When Redis is
    unavailable, operations transparently fall back to a local in-memory cache
    so request paths keep working.
    """

    def __init__(self, redis_url: str, default_ttl_seconds: int) -> None:
        self._default_ttl_seconds = max(default_ttl_seconds, 1)
        self._redis_url = redis_url
        self._redis: Redis | None = None
        self._fallback_store: dict[str, tuple[datetime, str]] = {}
        self._redis_backoff_until: datetime | None = None

    async def get(self, namespace: str, key: str) -> Any | None:
        cache_key = self._compose_key(namespace, key)
        payload = await self._redis_get(cache_key)
        if payload is None:
            payload = self._fallback_get_raw(cache_key)
            if payload is None:
                return None
        return json.loads(payload)

    async def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        cache_key = self._compose_key(namespace, key)
        ttl = max(ttl_seconds or self._default_ttl_seconds, 1)
        payload = json.dumps(value, default=str)

        if not await self._redis_set(cache_key, payload, ttl):
            self._fallback_set_raw(cache_key, payload, ttl)

    async def delete(self, namespace: str, key: str) -> None:
        cache_key = self._compose_key(namespace, key)
        await self._redis_delete(cache_key)
        self._fallback_store.pop(cache_key, None)

    async def invalidate(self, namespace: str) -> None:
        prefix = f"{namespace}:"
        await self._redis_invalidate(prefix)

        keys_to_delete = [key for key in self._fallback_store if key.startswith(prefix)]
        for key in keys_to_delete:
            self._fallback_store.pop(key, None)

    async def ping(self) -> bool:
        redis = await self._get_redis()
        if redis is None:
            return False

        try:
            return bool(await redis.ping())
        except RedisError:
            logger.warning("Redis ping failed", exc_info=True)
            return False

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
        self._redis_backoff_until = None

    def _compose_key(self, namespace: str, key: str) -> str:
        return f"{namespace}:{key}"

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
            except RedisError:
                logger.warning("Redis initialization failed", exc_info=True)
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
            logger.warning("Redis get failed for key=%s", key, exc_info=True)
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
            logger.warning("Redis set failed for key=%s", key, exc_info=True)
            self._set_redis_backoff()
            return False

    async def _redis_delete(self, key: str) -> None:
        redis = await self._get_redis()
        if redis is None:
            return

        try:
            await redis.delete(key)
        except RedisError:
            logger.warning("Redis delete failed for key=%s", key, exc_info=True)
            self._set_redis_backoff()

    async def _redis_invalidate(self, prefix: str) -> None:
        redis = await self._get_redis()
        if redis is None:
            return

        try:
            keys = [key async for key in redis.scan_iter(match=f"{prefix}*")]
            if keys:
                await redis.delete(*keys)
        except RedisError:
            logger.warning(
                "Redis invalidate failed for prefix=%s",
                prefix,
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
