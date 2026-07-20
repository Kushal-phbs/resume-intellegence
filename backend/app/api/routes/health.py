from fastapi import APIRouter

from app.config import settings

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
