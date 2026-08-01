import os

os.environ["DEBUG"] = "false"
os.environ["LLM_PROVIDER"] = "groq"
os.environ["GROQ_API_KEY"] = "test-key"
os.environ["GROQ_MODEL"] = "test-model"

from fastapi.testclient import TestClient

from app.api.routes import health
from app.db.dependency import get_db_session
from app.dependencies.cache import get_cache_service
from app.main import app


class DummySettings:
    llm_provider = "groq"
    groq_model = "test-model"
    environment = "development"
    app_version = "0.1.0"
    groq_api_key = "test-key"
    groq_base_url = "https://api.groq.com/openai/v1"


class _DbSessionOK:
    async def execute(self, _query) -> object:
        return object()


class _CacheOK:
    async def ping(self) -> bool:
        return True


async def _override_db_ok():
    yield _DbSessionOK()


def test_health_endpoint_returns_application_metadata(monkeypatch):
    monkeypatch.setattr(health, "settings", DummySettings)
    app.dependency_overrides[get_db_session] = _override_db_ok
    app.dependency_overrides[get_cache_service] = lambda: _CacheOK()

    try:
        client = TestClient(app)
        response = client.get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["provider"] == "groq"
    assert payload["model"] == "test-model"
    assert payload["environment"] == "development"
    assert payload["version"] == "0.1.0"
    assert payload["checks"]["postgresql"] == "ok"
    assert payload["checks"]["redis"] == "ok"
    assert payload["checks"]["groq_config"] == "ok"


def test_liveness_endpoint_returns_alive() -> None:
    client = TestClient(app)
    response = client.get("/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_endpoint_response_shape() -> None:
    client = TestClient(app)
    response = client.get("/ready")

    assert response.status_code in {200, 503}
    payload = response.json()
    assert payload["status"] in {"ready", "not_ready"}
    assert "checks" in payload
    assert "postgresql" in payload["checks"]
    assert "redis" in payload["checks"]
    assert "groq_config" in payload["checks"]
