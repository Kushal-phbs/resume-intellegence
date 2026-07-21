"""FastAPI dependency providers for database session access."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal

__all__ = ["get_db_session"]


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield an ``AsyncSession`` scoped to a single request.

    Commits on successful completion of the request and rolls back if an
    exception propagates out of the request handler. The session is always
    closed when the context manager exits.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
