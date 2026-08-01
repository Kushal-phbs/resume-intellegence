from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.chat import router as chat_router
from app.core.handlers import register_exception_handlers


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(chat_router)
    return app


def test_chat_paths_are_documented() -> None:
    openapi = TestClient(_build_app()).get("/openapi.json").json()

    assert "/chat/" in openapi["paths"]
    assert "/chat/conversations" in openapi["paths"]
    assert "/chat/conversations/{conversation_id}" in openapi["paths"]
    assert "/chat/conversations/{conversation_id}/messages" in openapi["paths"]
