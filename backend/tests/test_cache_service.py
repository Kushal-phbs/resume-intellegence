from __future__ import annotations

from uuid import uuid4

import pytest

from app.config import settings
from app.services.cache_service import CacheService


@pytest.mark.anyio
async def test_cache_service_set_get_delete_roundtrip() -> None:
    cache = CacheService(redis_url="redis://invalid:6379/0", default_ttl_seconds=30)

    await cache.set("ns", "key", {"value": 123})
    result = await cache.get("ns", "key")
    assert result == {"value": 123}

    await cache.delete("ns", "key")
    missing = await cache.get("ns", "key")
    assert missing is None


@pytest.mark.anyio
async def test_cache_service_invalidate_namespace() -> None:
    cache = CacheService(redis_url="redis://invalid:6379/0", default_ttl_seconds=30)

    suffix = str(uuid4())
    namespace = f"dashboard:{suffix}"
    await cache.set(namespace, "a", {"x": 1})
    await cache.set(namespace, "b", {"x": 2})

    assert await cache.get(namespace, "a") == {"x": 1}
    assert await cache.get(namespace, "b") == {"x": 2}

    await cache.invalidate(namespace)

    assert await cache.get(namespace, "a") is None
    assert await cache.get(namespace, "b") is None


@pytest.mark.anyio
async def test_cache_service_graceful_fallback_when_redis_unavailable() -> None:
    cache = CacheService(redis_url="redis://127.0.0.1:1/0", default_ttl_seconds=30)

    await cache.set("resume", "latest", {"ok": True})
    assert await cache.get("resume", "latest") == {"ok": True}


@pytest.mark.anyio
async def test_cache_service_namespace_invalidation_is_scoped() -> None:
    cache = CacheService(redis_url="redis://invalid:6379/0", default_ttl_seconds=30)

    await cache.set("ns_a", "k1", {"value": "a"})
    await cache.set("ns_b", "k1", {"value": "b"})

    await cache.invalidate("ns_a")

    assert await cache.get("ns_a", "k1") is None
    assert await cache.get("ns_b", "k1") == {"value": "b"}


@pytest.mark.anyio
async def test_cache_service_ping_returns_false_when_redis_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "redis_enabled", False)

    cache = CacheService(redis_url="redis://localhost:6379/0", default_ttl_seconds=30)
    assert await cache.ping() is False

    monkeypatch.setattr(settings, "redis_enabled", True)
