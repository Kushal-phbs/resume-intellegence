from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.resume_tailoring import export_router
from app.api.routes.resume_tailoring import router as tailoring_router
from app.core.handlers import register_exception_handlers


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(tailoring_router)
    app.include_router(export_router)
    return app


def test_resume_tailoring_paths_are_documented() -> None:
    openapi = TestClient(_build_app()).get("/openapi.json").json()

    assert "/resume-tailoring/{resume_id}/{job_id}" in openapi["paths"]
    assert "/resume-tailoring/history" in openapi["paths"]
    assert "/resume-tailoring/{session_id}" in openapi["paths"]
    assert "/resume-tailoring/{session_id}/resume" in openapi["paths"]
    assert "/resume-tailoring/{session_id}/cover-letter" in openapi["paths"]
    assert "/export/resume/{version_id}" in openapi["paths"]
    assert "/export/cover-letter/{cover_letter_id}" in openapi["paths"]


def test_resume_tailoring_openapi_exposes_bearer_auth() -> None:
    openapi = TestClient(_build_app()).get("/openapi.json").json()
    schemes = openapi.get("components", {}).get("securitySchemes", {})

    assert "HTTPBearer" in schemes
    assert schemes["HTTPBearer"]["type"] == "http"
    assert schemes["HTTPBearer"]["scheme"] == "bearer"
