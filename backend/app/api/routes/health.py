from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.dependency import get_db_session
from app.dependencies.cache import get_cache_service
from app.services.cache_service import CacheService

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return lightweight application health metadata without external calls."""
    return {
        "status": "healthy",
        "provider": settings.llm_provider,
        "model": settings.groq_model,
        "environment": settings.environment,
        "version": settings.app_version,
    }


@router.get("/ready")
async def readiness_check(
    db_session: AsyncSession = Depends(get_db_session),
    cache_service: CacheService = Depends(get_cache_service),
) -> JSONResponse:
    """Validate external dependencies required to serve traffic."""
    db_ok = True
    redis_ok = await cache_service.ping()

    try:
        await db_session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    ready = db_ok and redis_ok
    payload = {
        "status": "ready" if ready else "not_ready",
        "checks": {
            "postgresql": "ok" if db_ok else "failed",
            "redis": "ok" if redis_ok else "failed",
        },
    }

    return JSONResponse(
        content=payload,
        status_code=(
            status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
    )


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    """Return process liveness without external dependency checks."""
    return {"status": "alive"}
