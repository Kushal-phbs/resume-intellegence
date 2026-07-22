from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""

    logger.info("Application starting")

    try:
        yield
    finally:
        from app.dependencies.cache import (
            get_cache_service,
            get_rate_limiter_service,
        )

        await get_cache_service().close()
        await get_rate_limiter_service().close()
        logger.info("Application shutting down")
