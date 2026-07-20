"""Lightweight middleware for request correlation IDs."""

from __future__ import annotations

import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger, request_id_ctx


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
