import logging
import os
import re
import sqlite3
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.handlers import register_exception_handlers
from app.core.logging import (
    JsonFormatter,
    RedactionFilter,
    RequestIdFilter,
    request_id_ctx,
)
from app.core.middleware import RequestIDMiddleware
from app.main import app

os.environ["DEBUG"] = "false"
os.environ["GROQ_API_KEY"] = "test-key"
os.environ["GROQ_MODEL"] = "test-model"
os.environ["LLM_PROVIDER"] = "groq"


def test_request_id_middleware_adds_header() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert re.match(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        response.headers["X-Request-ID"],
    )
    json_body = response.json()
    assert json_body["status"] in {"healthy", "degraded"}
    assert "provider" in json_body
    assert "model" in json_body
    assert "environment" in json_body
    assert "version" in json_body


def test_request_id_filter_attaches_request_id_to_log_record() -> None:
    request_id_ctx.set("test-request-id")

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )

    filter_result = RequestIdFilter().filter(record)

    assert filter_result is True
    assert record.request_id == "test-request-id"


def test_request_id_header_on_validation_error() -> None:
    response = TestClient(app).post("/chat/", json={})

    assert response.status_code == 422
    assert response.headers["X-Request-ID"]
    payload = response.json()
    assert payload["detail"] == "Request validation error"
    assert payload["error"]["code"] == "RequestValidationError"
    for error in payload["error"]["errors"]:
        assert "input" not in error


def test_request_id_header_on_unhandled_exception() -> None:
    local_app = FastAPI()
    local_app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(local_app)

    @local_app.get("/fail")
    async def fail() -> None:
        raise RuntimeError("boom")

    client = TestClient(local_app, raise_server_exceptions=False)
    response = client.get("/fail")

    assert response.status_code == 500
    assert response.headers["X-Request-ID"]
    payload = response.json()
    assert payload["detail"] == "Internal server error"
    assert payload["error"]["code"] == "InternalServerError"


def test_redaction_filter_masks_secret_like_values() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="Authorization=Bearer abc123 token=xyz secret=hunter2",
        args=(),
        exc_info=None,
    )

    accepted = RedactionFilter().filter(record)

    assert accepted is True
    message = str(record.msg)
    assert "abc123" not in message
    assert "xyz" not in message
    assert "hunter2" not in message
    assert "[REDACTED]" in message


def test_request_id_filter_marks_database_failures() -> None:
    exc_info = None
    try:
        raise sqlite3.OperationalError("database is locked")
    except sqlite3.OperationalError:
        exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="db failure",
            args=(),
            exc_info=exc_info,
        )

    RequestIdFilter().filter(record)
    assert record.failure_domain == "database"


def test_json_formatter_outputs_structured_payload() -> None:
    request_id_ctx.set("req-123")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request.completed",
        args=(),
        exc_info=None,
    )
    RequestIdFilter().filter(record)

    payload = JsonFormatter().format(record)

    assert '"request_id": "req-123"' in payload
    assert '"ai_latency_ms":' in payload
    assert '"message": "request.completed"' in payload
