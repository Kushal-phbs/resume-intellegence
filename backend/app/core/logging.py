"""Reusable logging setup for the backend application.

Provides setup_logging() to configure the root logger once. Default level is INFO.
Log messages include timestamp, level, logger name and message.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar

__all__ = ["setup_logging", "logger"]

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LEVEL = logging.INFO

# Module-level logger for this module; other modules should get their own named loggers.
logger = logging.getLogger(__name__)

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """Attach the current request ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get("-")
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
