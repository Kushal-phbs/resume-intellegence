import os

os.environ["DEBUG"] = "false"
os.environ["LLM_PROVIDER"] = "groq"
os.environ["GROQ_API_KEY"] = "test-key"
os.environ["GROQ_MODEL"] = "test-model"

from fastapi.testclient import TestClient

from app.api.routes import health
from app.main import app


class DummySettings:
    llm_provider = "groq"
    groq_model = "test-model"
    environment = "development"
    app_version = "0.1.0"


def test_health_endpoint_returns_application_metadata(monkeypatch):
    monkeypatch.setattr(health, "settings", DummySettings)

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "provider": "groq",
        "model": "test-model",
        "environment": "development",
        "version": "0.1.0",
    }


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
