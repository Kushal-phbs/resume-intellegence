from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.dashboard import router as dashboard_router
from app.core.handlers import register_exception_handlers
from app.dependencies.dashboard import get_dashboard_service


class _NoopDashboardService:
    async def get_dashboard_summary(self, **_kwargs):
        raise RuntimeError("service should not be called without auth")


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(dashboard_router)
    app.dependency_overrides[get_dashboard_service] = lambda: _NoopDashboardService()
    return app


def test_dashboard_requires_authentication() -> None:
    response = TestClient(_build_app()).get("/dashboard")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"
