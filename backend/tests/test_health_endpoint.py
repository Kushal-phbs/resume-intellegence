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
