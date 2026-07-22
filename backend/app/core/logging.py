"""Reusable logging setup for the backend application.

Provides setup_logging() to configure the root logger once. Default level is INFO.
Log messages include timestamp, level, logger name and message.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar

__all__ = [
    "setup_logging",
    "logger",
    "request_id_ctx",
    "user_id_ctx",
    "endpoint_ctx",
    "method_ctx",
    "status_code_ctx",
    "execution_time_ms_ctx",
    "ai_processing_duration_ms_ctx",
]

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | request_id=%(request_id)s "
    "user_id=%(user_id)s method=%(method)s endpoint=%(endpoint)s "
    "status=%(status_code)s duration_ms=%(execution_time_ms)s "
    "ai_duration_ms=%(ai_processing_duration_ms)s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LEVEL = logging.INFO

# Module-level logger for this module; other modules should get their own named loggers.
logger = logging.getLogger(__name__)

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="-")
endpoint_ctx: ContextVar[str] = ContextVar("endpoint", default="-")
method_ctx: ContextVar[str] = ContextVar("method", default="-")
status_code_ctx: ContextVar[str] = ContextVar("status_code", default="-")
execution_time_ms_ctx: ContextVar[str] = ContextVar("execution_time_ms", default="-")
ai_processing_duration_ms_ctx: ContextVar[str] = ContextVar(
    "ai_processing_duration_ms",
    default="0.0",
)


class RequestIdFilter(logging.Filter):
    """Attach current request context values to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get("-")
        record.user_id = user_id_ctx.get("-")
        record.endpoint = endpoint_ctx.get("-")
        record.method = method_ctx.get("-")
        record.status_code = status_code_ctx.get("-")
        record.execution_time_ms = execution_time_ms_ctx.get("-")
        record.ai_processing_duration_ms = ai_processing_duration_ms_ctx.get("0.0")
        return True


def setup_logging(level: int | str = DEFAULT_LEVEL) -> None:
    """Configure the root logger once.

    If the root logger already has handlers configured this function returns immediately
    to avoid attaching duplicate handlers (idempotent behavior).

    Args:
        level: Logging level (int or str) to set on the root logger.
            Defaults to logging.INFO.
    """
    root = logging.getLogger()

    # Normalize string levels like "info" -> logging.INFO
    if isinstance(level, str):
        level = logging.getLevelName(level.upper())

    root.setLevel(level)

    # If handlers already exist on the root logger, assume logging is configured.
    if root.handlers:
        return

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.addFilter(RequestIdFilter())
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
    handler.setFormatter(formatter)

    root.addHandler(handler)
