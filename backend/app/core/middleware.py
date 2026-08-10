"""Middleware for request IDs, observability, and security headers."""

from __future__ import annotations

import uuid
from time import perf_counter

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import (
    ai_processing_duration_ms_ctx,
    endpoint_ctx,
    execution_time_ms_ctx,
    logger,
    method_ctx,
    request_id_ctx,
    status_code_ctx,
    user_id_ctx,
)
from app.core.metrics import active_requests, http_request_count, http_request_latency


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that generates and propagates a request correlation ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Assign a request id to context/state and include it in response headers."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        token = request_id_ctx.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)

        response.headers["X-Request-ID"] = request_id
        logger.debug("Assigned request ID %s to incoming request", request_id)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach baseline hardening headers to every HTTP response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Apply default security headers to outgoing responses."""
        response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")

        # Only send HSTS over HTTPS
        if request.url.scheme == "https":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        # Skip CSP for FastAPI documentation pages
        if not request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            response.headers.setdefault(
                "Content-Security-Policy",
                (
                    "default-src 'self'; "
                    "frame-ancestors 'none'; "
                    "base-uri 'self'; "
                    "object-src 'none';"
                ),
            )

        return response


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Capture request timing, emit structured logs, and record Prometheus metrics."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Capture request telemetry and attach processing-time headers."""
        method_token = method_ctx.set(request.method)
        endpoint_token = endpoint_ctx.set(request.url.path)
        status_token = status_code_ctx.set("-")
        duration_token = execution_time_ms_ctx.set("-")
        ai_duration_token = ai_processing_duration_ms_ctx.set("0.0")

        active_requests.inc()
        started = perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            active_requests.dec()
            elapsed_ms = round((perf_counter() - started) * 1000, 2)
            elapsed_sec = elapsed_ms / 1000.0
            execution_time_ms_ctx.set(str(elapsed_ms))
            status_code_ctx.set(str(status_code))

            user_id = getattr(request.state, "user_id", "-")
            user_id_ctx.set(str(user_id))
            logger.info("request.completed")

            # Record Prometheus metrics (skip /metrics to avoid recursion)
            if request.url.path != "/metrics":
                http_request_count.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=str(status_code),
                ).inc()
                http_request_latency.labels(
                    method=request.method,
                    endpoint=request.url.path,
                ).observe(elapsed_sec)

            ai_processing_duration_ms_ctx.reset(ai_duration_token)
            execution_time_ms_ctx.reset(duration_token)
            status_code_ctx.reset(status_token)
            endpoint_ctx.reset(endpoint_token)
            method_ctx.reset(method_token)

        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        response.headers["Server-Timing"] = f"app;dur={elapsed_ms:.2f}"
        return response
