from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware import SecurityHeadersMiddleware


def test_security_headers_middleware_adds_expected_headers() -> None:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(app).get("/ping")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in response.headers
    assert response.headers["X-XSS-Protection"] == "1; mode=block"


def test_security_headers_middleware_preserves_response_body() -> None:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/payload")
    async def payload() -> dict[str, str]:
        return {"message": "ok"}

    response = TestClient(app).get("/payload")

    assert response.status_code == 200
    assert response.json() == {"message": "ok"}
