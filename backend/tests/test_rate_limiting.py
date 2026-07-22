from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.config.settings import settings
from app.core.handlers import register_exception_handlers
from app.dependencies.rate_limit import limit


def _create_test_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    router = APIRouter(prefix="/rate")
    bucket = f"test_bucket_{uuid4().hex}"

    @router.post(
        "/test",
        dependencies=[Depends(limit(bucket=bucket, requests=2, window_seconds=60))],
    )
    async def limited_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    return app


def test_rate_limit_returns_429_after_limit_exceeded(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_enabled", True)

    app = _create_test_app()
    client = TestClient(app)

    assert client.post("/rate/test").status_code == 200
    assert client.post("/rate/test").status_code == 200

    response = client.post("/rate/test")
    assert response.status_code == 429
    assert response.json()["detail"] == "Rate limit exceeded"
    assert "Retry-After" in response.headers


def test_rate_limit_headers_are_present(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_enabled", True)

    app = _create_test_app()
    client = TestClient(app)

    response = client.post("/rate/test")
    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_rate_limit_response_contains_structured_error(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_enabled", True)

    app = _create_test_app()
    client = TestClient(app)

    client.post("/rate/test")
    client.post("/rate/test")
    response = client.post("/rate/test")

    assert response.status_code == 429
    payload = response.json()
    assert payload["detail"] == "Rate limit exceeded"
    assert payload["error"]["code"] == "RateLimitException"


def test_rate_limit_remaining_header_decrements(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_enabled", True)

    app = _create_test_app()
    client = TestClient(app)

    first = client.post("/rate/test")
    second = client.post("/rate/test")

    assert first.status_code == 200
    assert second.status_code == 200
    assert int(first.headers["X-RateLimit-Remaining"]) >= int(
        second.headers["X-RateLimit-Remaining"]
    )


def test_rate_limit_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_enabled", False)

    app = _create_test_app()
    client = TestClient(app)

    for _ in range(5):
        assert client.post("/rate/test").status_code == 200

    monkeypatch.setattr(settings, "rate_limit_enabled", True)
