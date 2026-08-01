from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.notifications import router as notifications_router
from app.core.handlers import register_exception_handlers


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(notifications_router)
    return app


def test_notifications_paths_are_documented() -> None:
    openapi = TestClient(_build_app()).get("/openapi.json").json()

    assert "/notifications" in openapi["paths"]
    assert "/notifications/unread-count" in openapi["paths"]
    assert "/notifications/read-all" in openapi["paths"]
    assert "/notifications/{notification_id}/read" in openapi["paths"]
    assert "/notifications/{notification_id}" in openapi["paths"]
