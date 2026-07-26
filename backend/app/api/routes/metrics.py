"""Prometheus metrics endpoint."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.metrics import get_metrics

router = APIRouter()


@router.get("/metrics")
async def metrics_endpoint() -> PlainTextResponse:
    """Return Prometheus-compatible metrics."""
    return PlainTextResponse(
        content=get_metrics(),
        media_type="text/plain; version=0.0.4",
    )
