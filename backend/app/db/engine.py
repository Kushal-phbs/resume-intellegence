"""Async SQLAlchemy engine configuration.

A single module-level engine is created from the application settings and
reused across the process lifetime, following SQLAlchemy's recommended
"engine as a singleton" pattern.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config.settings import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
)

__all__ = ["engine"]
