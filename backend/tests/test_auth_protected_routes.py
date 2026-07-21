from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.config.settings import settings
from app.core.handlers import register_exception_handlers
from app.dependencies.auth import get_current_user, get_user_repository, require_admin
from app.enums import TokenType, UserRole
from app.schemas.auth import CurrentUserResponse
from app.services.jwt_service import JWTService


class _UserRepositoryStub:
    def __init__(self, users: dict[str, SimpleNamespace] | None = None) -> None:
        self._users = users or {}

    async def get_by_id(self, user_id: object) -> SimpleNamespace | None:
        return self._users.get(str(user_id))


def _build_app(repo: _UserRepositoryStub) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    app.dependency_overrides[get_user_repository] = lambda: repo

    @app.get("/users/me", response_model=CurrentUserResponse)
    async def me_endpoint(
        current_user: SimpleNamespace = Depends(get_current_user),
    ) -> CurrentUserResponse:
        return CurrentUserResponse.model_validate(current_user)

    @app.get("/admin")
    async def admin_endpoint(
        _current_user: SimpleNamespace = Depends(require_admin),
    ) -> dict[str, str]:
        return {"status": "ok"}

    return app


def test_protected_route_authenticated_access() -> None:
    user_id = uuid4()
    now = datetime.now(UTC)
    user = SimpleNamespace(
        id=user_id,
        email="john@example.com",
        full_name="John Doe",
        role=UserRole.USER.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    app = _build_app(_UserRepositoryStub({str(user_id): user}))
    token = JWTService().create_access_token(
        subject=str(user_id),
        role=UserRole.USER.value,
    )

    response = TestClient(app).get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "john@example.com"
    assert response.json()["role"] == UserRole.USER.value


def test_protected_route_missing_token() -> None:
    app = _build_app(_UserRepositoryStub())

    response = TestClient(app).get("/users/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_protected_route_malformed_token() -> None:
    app = _build_app(_UserRepositoryStub())

    response = TestClient(app).get(
        "/users/me",
        headers={"Authorization": "Bearer malformed-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication token"


def test_protected_route_expired_token() -> None:
    app = _build_app(_UserRepositoryStub())
    now = datetime.now(UTC)
    expired_token = jwt.encode(
        {
            "sub": str(uuid4()),
            "type": TokenType.ACCESS.value,
            "role": UserRole.USER.value,
            "iat": int((now - timedelta(minutes=10)).timestamp()),
            "exp": int((now - timedelta(minutes=1)).timestamp()),
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = TestClient(app).get(
        "/users/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication token has expired"


def test_protected_route_invalid_signature() -> None:
    app = _build_app(_UserRepositoryStub())
    now = datetime.now(UTC)
    invalid_signature_token = jwt.encode(
        {
            "sub": str(uuid4()),
            "type": TokenType.ACCESS.value,
            "role": UserRole.USER.value,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        "wrong-secret",
        algorithm=settings.jwt_algorithm,
    )

    response = TestClient(app).get(
        "/users/me",
        headers={"Authorization": f"Bearer {invalid_signature_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication token"


def test_admin_authorization_requires_admin_role() -> None:
    user_id = uuid4()
    now = datetime.now(UTC)
    user = SimpleNamespace(
        id=user_id,
        email="john@example.com",
        full_name="John Doe",
        role=UserRole.USER.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    app = _build_app(_UserRepositoryStub({str(user_id): user}))
    token = JWTService().create_access_token(
        subject=str(user_id),
        role=UserRole.USER.value,
    )

    response = TestClient(app).get(
        "/admin",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_admin_authorization_allows_admin_role() -> None:
    user_id = uuid4()
    now = datetime.now(UTC)
    user = SimpleNamespace(
        id=user_id,
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.ADMIN.value,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    app = _build_app(_UserRepositoryStub({str(user_id): user}))
    token = JWTService().create_access_token(
        subject=str(user_id),
        role=UserRole.ADMIN.value,
    )

    response = TestClient(app).get(
        "/admin",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_exposes_http_bearer_security_scheme() -> None:
    app = _build_app(_UserRepositoryStub())

    openapi = TestClient(app).get("/openapi.json").json()
    schemes = openapi.get("components", {}).get("securitySchemes", {})

    assert "HTTPBearer" in schemes
    assert schemes["HTTPBearer"]["type"] == "http"
    assert schemes["HTTPBearer"]["scheme"] == "bearer"
