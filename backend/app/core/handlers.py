"""Global exception handlers for the FastAPI application.

Provides handlers for AppException (application errors), RequestValidationError
(validation errors produced by FastAPI/Pydantic) and a catch-all Exception handler
that logs unexpected errors and returns a consistent JSON response.

Expose register_exception_handlers(app) to attach handlers to a FastAPI app.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException
from app.core.logging import logger


def _attach_request_id_header(response: JSONResponse, request: Request) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    if request_id is not None:
        response.headers["X-Request-ID"] = request_id
    return response


def _base_error_content(
    *,
    request: Request,
    detail: str,
    code: str,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "detail": detail,
        "error": {
            "code": code,
            "timestamp": datetime.now(UTC).isoformat(),
            "path": str(request.url.path),
            "method": request.method,
            "request_id": getattr(request.state, "request_id", None),
        },
    }
    if extras:
        payload["error"].update(extras)
    return payload


def _sanitize_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return validation errors without echoing user-provided input values."""
    sanitized: list[dict[str, Any]] = []
    for item in errors:
        sanitized_item = {
            key: value for key, value in item.items() if key not in {"input", "url"}
        }
        ctx = sanitized_item.get("ctx")
        if isinstance(ctx, dict):
            sanitized_item["ctx"] = {
                key: value
                for key, value in ctx.items()
                if "secret" not in key.lower() and "token" not in key.lower()
            }
        sanitized.append(sanitized_item)
    return sanitized


def _app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle AppException and return a JSON response using its status_code."""
    content = _base_error_content(
        request=request,
        detail=exc.message,
        code=exc.__class__.__name__,
    )
    response = JSONResponse(status_code=exc.status_code, content=content)
    retry_after = getattr(exc, "retry_after_seconds", None)
    if isinstance(retry_after, int):
        response.headers["Retry-After"] = str(max(retry_after, 1))
    return _attach_request_id_header(response, request)


def _validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors and return structured JSON with details."""
    content = _base_error_content(
        request=request,
        detail="Request validation error",
        code="RequestValidationError",
        extras={"errors": _sanitize_validation_errors(exc.errors())},
    )
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=content
    )
    return _attach_request_id_header(response, request)


def _generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected exceptions.

    Logs the exception and returns a 500 response.
    """
    # Use the module-level logger for structured logs.
    # Fall back to stdlib logging if needed.
    try:
        logger.exception(
            "Unhandled exception while processing request: %s %s",
            request.method,
            request.url.path,
        )
    except Exception:  # pragma: no cover - defensive fallback
        logging.exception("Unhandled exception while processing request")

    content = _base_error_content(
        request=request,
        detail="Internal server error",
        code="InternalServerError",
    )
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content
    )
    return _attach_request_id_header(response, request)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI application.

    Call this early in application setup (for example, after creating FastAPI).
    """
    app.add_exception_handler(AppException, _app_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _generic_exception_handler)


__all__ = ["register_exception_handlers"]
