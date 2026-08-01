"""Tests for the Prometheus metrics endpoint and metric recording."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestMetricsEndpoint:
    """Verify the /metrics endpoint returns Prometheus-formatted output."""

    def test_metrics_endpoint_returns_200(self) -> None:
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")

    def test_metrics_contains_expected_counters(self) -> None:
        response = client.get("/metrics")
        text = response.text
        assert "# HELP http_requests_total" in text
        assert "# TYPE http_requests_total counter" in text
        assert "# HELP http_active_requests" in text
        assert "# TYPE http_active_requests gauge" in text
        assert "# HELP http_request_duration_seconds" in text
        assert "# TYPE http_request_duration_seconds histogram" in text

    def test_metrics_contains_ai_metrics(self) -> None:
        response = client.get("/metrics")
        text = response.text
        assert "# HELP ai_requests_total" in text
        assert "# TYPE ai_requests_total counter" in text
        assert "# HELP ai_request_duration_seconds" in text
        assert 'ai_requests_total{provider="groq"} 0.0' in text

    def test_metrics_contains_db_metrics(self) -> None:
        response = client.get("/metrics")
        text = response.text
        assert "# HELP db_queries_total" in text
        assert "# TYPE db_queries_total counter" in text

    def test_metrics_contains_cache_metrics(self) -> None:
        response = client.get("/metrics")
        text = response.text
        assert "# HELP cache_hits_total" in text
        assert "# TYPE cache_hits_total counter" in text
        assert "# HELP cache_misses_total" in text
        assert 'cache_hits_total{namespace="global"} 0.0' in text
        assert 'cache_misses_total{namespace="global"} 0.0' in text

    def test_metrics_contains_rate_limit_metrics(self) -> None:
        response = client.get("/metrics")
        text = response.text
        assert "# HELP rate_limit_violations_total" in text
        assert "# TYPE rate_limit_violations_total counter" in text

    def test_request_records_http_metrics(self) -> None:
        # Make a request to a known endpoint
        client.get("/live")
        response = client.get("/metrics")
        text = response.text
        # The /live request should have been counted
        assert 'http_requests_total{endpoint="/live"' in text

    def test_metrics_does_not_self_record(self) -> None:
        """Accessing /metrics should not create a metric for /metrics."""
        client.get("/metrics")
        response = client.get("/metrics")
        text = response.text
        # Count occurrences of endpoint="/metrics" in http_requests_total
        count = text.count('endpoint="/metrics"')
        # Should be 0 since /metrics is excluded from self-recording
        assert count == 0


class TestMetricsContextManagers:
    """Verify the track_db_query and track_ai_request context managers."""

    def test_track_db_query_records_metric(self) -> None:
        from app.core.metrics import track_db_query

        with track_db_query("select"):
            pass

        response = client.get("/metrics")
        assert 'db_queries_total{operation="select"}' in response.text

    def test_track_ai_request_records_metric(self) -> None:
        from app.core.metrics import track_ai_request

        with track_ai_request("groq"):
            pass

        response = client.get("/metrics")
        assert 'ai_requests_total{provider="groq"}' in response.text
