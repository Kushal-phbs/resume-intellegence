"""Prometheus-compatible application metrics."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator

from prometheus_client import Counter, Gauge, Histogram, generate_latest

# HTTP metrics
http_request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "endpoint", "status"],
)

http_request_latency = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    labelnames=["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

active_requests = Gauge(
    "http_active_requests",
    "Number of active HTTP requests",
)

# AI/provider metrics
ai_request_count = Counter(
    "ai_requests_total",
    "Total AI provider requests",
    labelnames=["provider"],
)

ai_request_latency = Histogram(
    "ai_request_duration_seconds",
    "AI provider request latency in seconds",
    labelnames=["provider"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

# Database metrics
db_query_count = Counter(
    "db_queries_total",
    "Total database queries",
    labelnames=["operation"],
)

db_query_latency = Histogram(
    "db_query_duration_seconds",
    "Database query latency in seconds",
    labelnames=["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

# Cache metrics
cache_hits = Counter(
    "cache_hits_total",
    "Total cache hits",
    labelnames=["namespace"],
)

cache_misses = Counter(
    "cache_misses_total",
    "Total cache misses",
    labelnames=["namespace"],
)

# Rate-limit metrics
rate_limit_violations = Counter(
    "rate_limit_violations_total",
    "Total rate-limit violations",
    labelnames=["bucket"],
)


def get_metrics() -> bytes:
    """Return Prometheus-formatted metrics."""
    return generate_latest()


@contextmanager
def track_db_query(operation: str) -> Generator[None, None, None]:
    """Context manager to track a database query."""
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed = time.monotonic() - start
        db_query_count.labels(operation=operation).inc()
        db_query_latency.labels(operation=operation).observe(elapsed)


@contextmanager
def track_ai_request(provider: str) -> Generator[None, None, None]:
    """Context manager to track an AI provider request."""
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed = time.monotonic() - start
        ai_request_count.labels(provider=provider).inc()
        ai_request_latency.labels(provider=provider).observe(elapsed)
