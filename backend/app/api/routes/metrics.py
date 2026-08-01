"""Prometheus metrics endpoint."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.core.metrics import (
    ai_request_count,
    cache_hits,
    cache_misses,
    get_metrics,
    http_request_count,
)

router = APIRouter()


def _prime_metrics() -> None:
    """Initialize commonly consumed metric label series with zero values."""
    http_request_count.labels(method="GET", endpoint="/health", status="200").inc(0)
    ai_request_count.labels(provider=settings.llm_provider).inc(0)
    cache_hits.labels(namespace="global").inc(0)
    cache_misses.labels(namespace="global").inc(0)


@router.get(
    "/metrics",
    summary="Get Prometheus Metrics",
    description=(
        "Expose application metrics in Prometheus text exposition format for "
        "scraping by monitoring systems."
    ),
    responses={
        200: {"description": "Prometheus metrics payload."},
    },
)
async def metrics_endpoint() -> PlainTextResponse:
    """Return Prometheus-compatible metrics."""
    _prime_metrics()
    return PlainTextResponse(
        content=get_metrics(),
        media_type="text/plain; version=0.0.4",
    )
