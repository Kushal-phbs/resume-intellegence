from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.enums import TokenType, UserRole
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenPayload,
    TokenResponse,
)


def test_register_request_valid_payload() -> None:
    payload = RegisterRequest(
        email="user@example.com",
        password="StrongPass123!",
        full_name="John Doe",
    )

    assert payload.email == "user@example.com"
    assert payload.password == "StrongPass123!"
    assert payload.full_name == "John Doe"


def test_register_request_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="user@example.com",
            password="short",
            full_name="John Doe",
        )


def test_login_request_valid_payload() -> None:
    payload = LoginRequest(email="user@example.com", password="StrongPass123!")

    assert payload.email == "user@example.com"
    assert payload.password == "StrongPass123!"


def test_refresh_token_request_requires_token() -> None:
    with pytest.raises(ValidationError):
        RefreshTokenRequest(refresh_token="")


def test_token_response_defaults_to_bearer() -> None:
    payload = TokenResponse(
        access_token="access-token-value",
        refresh_token="refresh-token-value",
    )

    assert payload.token_type == "bearer"


def test_token_response_rejects_non_bearer_type() -> None:
    with pytest.raises(ValidationError):
        TokenResponse(
            access_token="access-token-value",
            refresh_token="refresh-token-value",
            token_type="jwt",
        )


def test_token_payload_accepts_access_type_with_role() -> None:
    payload = TokenPayload(
        sub="user-1",
        type=TokenType.ACCESS,
        role=UserRole.ADMIN,
        iat=1735689600,
        exp=1735690500,
    )

    assert payload.type == TokenType.ACCESS
    assert payload.role == UserRole.ADMIN
    assert payload.model_dump()["type"] == TokenType.ACCESS.value
    assert payload.model_dump()["role"] == UserRole.ADMIN.value


def test_token_payload_accepts_refresh_type_without_role() -> None:
    payload = TokenPayload(
        sub="user-1",
        type=TokenType.REFRESH,
        iat=1735689600,
        exp=1736294400,
    )

    assert payload.type == TokenType.REFRESH
    assert payload.model_dump()["type"] == TokenType.REFRESH.value
    assert payload.role is None


def test_token_payload_rejects_invalid_type() -> None:
    with pytest.raises(ValidationError):
        TokenPayload(
            sub="user-1",
            type="custom",
            iat=1735689600,
            exp=1736294400,
        )
