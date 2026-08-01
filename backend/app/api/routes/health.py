from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.dependency import get_db_session
from app.dependencies.cache import get_cache_service
from app.services.cache_service import CacheService

router = APIRouter()


def _is_groq_configured() -> bool:
    if settings.llm_provider.lower() != "groq":
        return True

    has_required = bool(settings.groq_api_key and settings.groq_model)
    has_valid_url = settings.groq_base_url.startswith(("http://", "https://"))
    return has_required and has_valid_url


async def _database_ok(db_session: AsyncSession) -> bool:
    try:
        await db_session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@router.get(
    "/health",
    summary="Get Service Health",
    description=(
        "Return application health status and dependency checks for PostgreSQL, "
        "Redis, and LLM provider configuration."
    ),
    responses={
        200: {"description": "Health payload returned successfully."},
    },
)
async def health_check(
    db_session: AsyncSession = Depends(get_db_session),
    cache_service: CacheService = Depends(get_cache_service),
) -> dict[str, object]:
    """Return application health metadata with dependency checks."""
    db_ok = await _database_ok(db_session)
    redis_ok = await cache_service.ping()
    groq_ok = _is_groq_configured()

    return {
        "status": "healthy" if (db_ok and redis_ok and groq_ok) else "degraded",
        "provider": settings.llm_provider,
        "model": settings.groq_model,
        "environment": settings.environment,
        "version": settings.app_version,
        "checks": {
            "postgresql": "ok" if db_ok else "failed",
            "redis": "ok" if redis_ok else "failed",
            "groq_config": "ok" if groq_ok else "failed",
        },
    }


@router.get(
    "/ready",
    summary="Get Readiness Status",
    description=(
        "Validate required downstream dependencies and return whether the "
        "service is ready to accept traffic."
    ),
    responses={
        200: {"description": "Service is ready to serve requests."},
        503: {"description": "One or more dependencies are unavailable."},
    },
)
async def readiness_check(
    db_session: AsyncSession = Depends(get_db_session),
    cache_service: CacheService = Depends(get_cache_service),
) -> JSONResponse:
    """Validate external dependencies required to serve traffic."""
    db_ok = await _database_ok(db_session)
    redis_ok = await cache_service.ping()
    groq_ok = _is_groq_configured()

    ready = db_ok and redis_ok and groq_ok
    payload = {
        "status": "ready" if ready else "not_ready",
        "checks": {
            "postgresql": "ok" if db_ok else "failed",
            "redis": "ok" if redis_ok else "failed",
            "groq_config": "ok" if groq_ok else "failed",
        },
    }

    return JSONResponse(
        content=payload,
        status_code=(
            status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
    )


@router.get(
    "/live",
    summary="Get Liveness Status",
    description="Return process liveness without checking external dependencies.",
    responses={
        200: {"description": "Process is running."},
    },
)
async def liveness_check() -> dict[str, str]:
    """Return process liveness without external dependency checks."""
    return {"status": "alive"}
