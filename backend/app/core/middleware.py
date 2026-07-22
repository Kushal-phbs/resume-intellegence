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


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that generates and propagates a request correlation ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
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
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        return response


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Capture request timing and emit centralized structured request logs."""

    async def dispatch(self, request: Request, call_next) -> Response:
        method_token = method_ctx.set(request.method)
        endpoint_token = endpoint_ctx.set(request.url.path)
        status_token = status_code_ctx.set("-")
        duration_token = execution_time_ms_ctx.set("-")
        ai_duration_token = ai_processing_duration_ms_ctx.set("0.0")

        started = perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            elapsed_ms = round((perf_counter() - started) * 1000, 2)
            execution_time_ms_ctx.set(str(elapsed_ms))
            status_code_ctx.set(str(status_code))

            user_id = getattr(request.state, "user_id", "-")
            user_id_ctx.set(str(user_id))
            logger.info("request.completed")

            ai_processing_duration_ms_ctx.reset(ai_duration_token)
            execution_time_ms_ctx.reset(duration_token)
            status_code_ctx.reset(status_token)
            endpoint_ctx.reset(endpoint_token)
            method_ctx.reset(method_token)

        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        response.headers["Server-Timing"] = f"app;dur={elapsed_ms:.2f}"
        return response
