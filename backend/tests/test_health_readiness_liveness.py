from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.routes import health
from app.db.dependency import get_db_session
from app.dependencies.cache import get_cache_service
from app.main import app


def test_liveness_endpoint_returns_alive() -> None:
    response = TestClient(app).get("/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_endpoint_returns_status_and_checks() -> None:
    response = TestClient(app).get("/ready")

    assert response.status_code in {200, 503}
    payload = response.json()
    assert payload["status"] in {"ready", "not_ready"}
    assert "checks" in payload
    assert "postgresql" in payload["checks"]
    assert "redis" in payload["checks"]
    assert "groq_config" in payload["checks"]


class _DbSessionOK:
    async def execute(self, _query) -> object:
        return object()


class _DbSessionFail:
    async def execute(self, _query) -> object:
        raise RuntimeError("db down")


class _CacheOK:
    async def ping(self) -> bool:
        return True


class _CacheFail:
    async def ping(self) -> bool:
        return False


async def _override_db_ok():
    yield _DbSessionOK()


async def _override_db_fail():
    yield _DbSessionFail()


def test_readiness_returns_200_when_db_and_redis_ok() -> None:
    original = health._is_groq_configured
    health._is_groq_configured = lambda: True
    app.dependency_overrides[get_db_session] = _override_db_ok
    app.dependency_overrides[get_cache_service] = lambda: _CacheOK()
    try:
        response = TestClient(app).get("/ready")
    finally:
        health._is_groq_configured = original
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_returns_503_when_db_fails() -> None:
    original = health._is_groq_configured
    health._is_groq_configured = lambda: True
    app.dependency_overrides[get_db_session] = _override_db_fail
    app.dependency_overrides[get_cache_service] = lambda: _CacheOK()
    try:
        response = TestClient(app).get("/ready")
    finally:
        health._is_groq_configured = original
        app.dependency_overrides.clear()

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["checks"]["postgresql"] == "failed"


def test_readiness_returns_503_when_redis_fails() -> None:
    original = health._is_groq_configured
    health._is_groq_configured = lambda: True
    app.dependency_overrides[get_db_session] = _override_db_ok
    app.dependency_overrides[get_cache_service] = lambda: _CacheFail()
    try:
        response = TestClient(app).get("/ready")
    finally:
        health._is_groq_configured = original
        app.dependency_overrides.clear()

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["checks"]["redis"] == "failed"


def test_readiness_returns_503_when_groq_configuration_fails() -> None:
    original = health._is_groq_configured
    health._is_groq_configured = lambda: False
    app.dependency_overrides[get_db_session] = _override_db_ok
    app.dependency_overrides[get_cache_service] = lambda: _CacheOK()
    try:
        response = TestClient(app).get("/ready")
    finally:
        health._is_groq_configured = original
        app.dependency_overrides.clear()

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["checks"]["groq_config"] == "failed"
