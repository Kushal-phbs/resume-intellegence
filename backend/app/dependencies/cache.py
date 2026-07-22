"""Dependency providers for cache and rate limiter services."""

from __future__ import annotations

from functools import lru_cache

from app.config import settings
from app.services.cache_service import CacheService
from app.services.rate_limiter_service import RateLimiterService


@lru_cache
def get_cache_service() -> CacheService:
    """Return a process-wide cache service instance."""
    return CacheService(
        redis_url=settings.redis_url,
        default_ttl_seconds=settings.cache_default_ttl_seconds,
    )


@lru_cache
def get_rate_limiter_service() -> RateLimiterService:
    """Return a process-wide rate limiter service instance."""
    return RateLimiterService(redis_url=settings.redis_url)
