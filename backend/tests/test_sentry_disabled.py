"""Tests that Sentry integration is disabled by default and does not break anything."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestSentryDisabled:
    """Verify the application works normally when Sentry is not configured."""

    def test_health_works_without_sentry(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_live_works_without_sentry(self) -> None:
        response = client.get("/live")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}

    def test_metrics_works_without_sentry(self) -> None:
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_sentry_dsn_defaults_to_empty(self) -> None:
        from app.config import settings

        assert settings.sentry_dsn == ""
