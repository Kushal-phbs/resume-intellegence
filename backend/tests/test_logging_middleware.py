from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware import ObservabilityMiddleware, RequestIDMiddleware


def test_observability_middleware_adds_timing_headers(caplog) -> None:
    app = FastAPI()
    app.add_middleware(ObservabilityMiddleware)
    app.add_middleware(RequestIDMiddleware)

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    with caplog.at_level(logging.INFO):
        response = TestClient(app).get("/ping")

    assert response.status_code == 200
    assert "X-Process-Time-Ms" in response.headers
    assert "Server-Timing" in response.headers
    assert any("request.completed" in record.message for record in caplog.records)


def test_observability_middleware_emits_timing_value_header() -> None:
    app = FastAPI()
    app.add_middleware(ObservabilityMiddleware)

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(app).get("/ping")

    assert response.status_code == 200
    value = float(response.headers["X-Process-Time-Ms"])
    assert value >= 0.0
