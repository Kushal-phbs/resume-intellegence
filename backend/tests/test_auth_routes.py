from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.auth import router as auth_router
from app.core.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    UserAlreadyExistsException,
)
from app.core.handlers import register_exception_handlers
from app.dependencies.auth import get_auth_service
from app.schemas.auth import TokenResponse


class _AuthServiceSuccessStub:
    async def register(self, _request: object) -> TokenResponse:
        return TokenResponse(access_token="access-1", refresh_token="refresh-1")

    async def login(self, _request: object) -> TokenResponse:
        return TokenResponse(access_token="access-2", refresh_token="refresh-2")

    async def refresh(self, _request: object) -> TokenResponse:
        return TokenResponse(access_token="access-3", refresh_token="refresh-3")


class _AuthServiceDuplicateStub:
    async def register(self, _request: object) -> TokenResponse:
        raise UserAlreadyExistsException()


class _AuthServiceInvalidCredentialsStub:
    async def login(self, _request: object) -> TokenResponse:
        raise InvalidCredentialsException()


class _AuthServiceInvalidRefreshStub:
    async def refresh(self, _request: object) -> TokenResponse:
        raise InvalidTokenException()


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(auth_router)
    return app


def test_register_route_success() -> None:
    app = _build_app()
    app.dependency_overrides[get_auth_service] = lambda: _AuthServiceSuccessStub()

    response = TestClient(app).post(
        "/auth/register",
        json={
            "email": "john@example.com",
            "password": "StrongPass123!",
            "full_name": "John Doe",
        },
    )

    assert response.status_code == 201
    assert response.json()["access_token"] == "access-1"
    assert response.json()["refresh_token"] == "refresh-1"
    assert response.json()["token_type"] == "bearer"


def test_register_route_duplicate_email() -> None:
    app = _build_app()
    app.dependency_overrides[get_auth_service] = lambda: _AuthServiceDuplicateStub()

    response = TestClient(app).post(
        "/auth/register",
        json={
            "email": "john@example.com",
            "password": "StrongPass123!",
            "full_name": "John Doe",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "A user with this email already exists"


def test_login_route_success() -> None:
    app = _build_app()
    app.dependency_overrides[get_auth_service] = lambda: _AuthServiceSuccessStub()

    response = TestClient(app).post(
        "/auth/login",
        json={
            "email": "john@example.com",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access-2"
    assert response.json()["refresh_token"] == "refresh-2"
    assert response.json()["token_type"] == "bearer"


def test_login_route_invalid_credentials() -> None:
    app = _build_app()
    app.dependency_overrides[get_auth_service] = lambda: (
        _AuthServiceInvalidCredentialsStub()
    )

    response = TestClient(app).post(
        "/auth/login",
        json={
            "email": "john@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_refresh_route_success() -> None:
    app = _build_app()
    app.dependency_overrides[get_auth_service] = lambda: _AuthServiceSuccessStub()

    response = TestClient(app).post(
        "/auth/refresh",
        json={"refresh_token": "some-refresh-token"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access-3"
    assert response.json()["refresh_token"] == "refresh-3"
    assert response.json()["token_type"] == "bearer"


def test_refresh_route_invalid_refresh_token() -> None:
    app = _build_app()
    app.dependency_overrides[get_auth_service] = lambda: (
        _AuthServiceInvalidRefreshStub()
    )

    response = TestClient(app).post(
        "/auth/refresh",
        json={"refresh_token": "bad-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication token"
