from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.dashboard import router as dashboard_router
from app.core.handlers import register_exception_handlers


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(dashboard_router)
    return app


def test_dashboard_paths_are_documented() -> None:
    openapi = TestClient(_build_app()).get("/openapi.json").json()

    assert "/dashboard" in openapi["paths"]
    assert "/dashboard/summary" in openapi["paths"]
    assert "/dashboard/activity" in openapi["paths"]
    assert "/dashboard/statistics" in openapi["paths"]
    assert "/dashboard/trends" in openapi["paths"]
    assert "/dashboard/performance" in openapi["paths"]
    assert "/dashboard/refresh" in openapi["paths"]


def test_dashboard_openapi_exposes_bearer_auth() -> None:
    openapi = TestClient(_build_app()).get("/openapi.json").json()
    schemes = openapi.get("components", {}).get("securitySchemes", {})

    assert "HTTPBearer" in schemes
    assert schemes["HTTPBearer"]["type"] == "http"
    assert schemes["HTTPBearer"]["scheme"] == "bearer"
