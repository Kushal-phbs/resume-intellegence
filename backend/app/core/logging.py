"""Reusable logging setup for the backend application.

Provides setup_logging() to configure the root logger once. Default level is INFO.
Log messages include timestamp, level, logger name and message.
"""

from __future__ import annotations

import json
import logging
import re
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

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

_SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(token\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(password\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(secret\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(x-api-key\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(groq_api_key\s*[:=]\s*)[^\s,;]+"),
]

_DB_ERROR_MODULE_MARKERS = (
    "sqlalchemy",
    "asyncpg",
    "psycopg",
    "psycopg2",
    "sqlite3",
)


def _classify_failure_domain(exc_info: Any) -> str:
    if not exc_info:
        return "-"

    exc_type = exc_info[0]
    if exc_type is None:
        return "-"

    module_name = getattr(exc_type, "__module__", "").lower()
    if any(marker in module_name for marker in _DB_ERROR_MODULE_MARKERS):
        return "database"

    if "redis" in module_name:
        return "cache"

    return "application"


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
        record.ai_latency_ms = ai_processing_duration_ms_ctx.get("0.0")
        record.failure_domain = _classify_failure_domain(record.exc_info)
        return True


class RedactionFilter(logging.Filter):
    """Best-effort log redaction for common secret patterns."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = str(record.msg)
        record.msg = self._redact_text(message)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    key: self._redact_value(value) for key, value in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(self._redact_value(value) for value in record.args)
            else:
                record.args = (self._redact_value(record.args),)
        return True

    def _redact_text(self, text: str) -> str:
        redacted = text
        for pattern in _SECRET_PATTERNS:
            redacted = pattern.sub(r"\1[REDACTED]", redacted)
        return redacted

    def _redact_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._redact_text(value)
        return value


class JsonFormatter(logging.Formatter):
    """Render logs as structured JSON payloads."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "request_id": getattr(record, "request_id", "-"),
            "user_id": getattr(record, "user_id", "-"),
            "method": getattr(record, "method", "-"),
            "endpoint": getattr(record, "endpoint", "-"),
            "status": getattr(record, "status_code", "-"),
            "duration_ms": getattr(record, "execution_time_ms", "-"),
            "ai_latency_ms": getattr(record, "ai_latency_ms", "0.0"),
            "failure_domain": getattr(record, "failure_domain", "-"),
        }

        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            payload["exception_type"] = (
                exc_type.__name__ if exc_type is not None else "Exception"
            )
            payload["exception_message"] = str(exc_value)

        return json.dumps(payload, ensure_ascii=True)


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
    handler.addFilter(RedactionFilter())
    handler.addFilter(RequestIdFilter())
    formatter = JsonFormatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
    handler.setFormatter(formatter)

    root.addHandler(handler)
