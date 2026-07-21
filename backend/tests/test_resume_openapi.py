from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.resume import router as resume_router
from app.core.handlers import register_exception_handlers


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(resume_router)
    return app


def test_resume_upload_endpoint_is_documented() -> None:
    openapi = TestClient(_build_app()).get("/openapi.json").json()

    upload_path = openapi["paths"]["/resumes/upload"]["post"]
    request_body = upload_path["requestBody"]

    assert "/resumes/upload" in openapi["paths"]
    assert "multipart/form-data" in request_body["content"]


def test_resume_api_exposes_bearer_security_scheme() -> None:
    openapi = TestClient(_build_app()).get("/openapi.json").json()
    schemes = openapi.get("components", {}).get("securitySchemes", {})

    assert "HTTPBearer" in schemes
    assert schemes["HTTPBearer"]["type"] == "http"
    assert schemes["HTTPBearer"]["scheme"] == "bearer"
