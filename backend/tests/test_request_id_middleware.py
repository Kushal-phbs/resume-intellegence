import logging
import os
import re

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.handlers import register_exception_handlers
from app.core.logging import RequestIdFilter, request_id_ctx
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
    assert json_body["status"] == "healthy"
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
