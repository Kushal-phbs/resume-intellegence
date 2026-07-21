from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config.settings import settings
from app.core.exceptions import InvalidTokenException, TokenExpiredException
from app.enums import TokenType, UserRole
from app.services.jwt_service import JWTService


def test_create_access_token_contains_expected_claims() -> None:
    service = JWTService()

    token = service.create_access_token(subject="user-123", role=UserRole.ADMIN.value)
    payload = service.decode_token(token)

    assert payload["sub"] == "user-123"
    assert payload["role"] == UserRole.ADMIN.value
    assert payload["type"] == TokenType.ACCESS.value
    assert isinstance(payload["iat"], int)
    assert isinstance(payload["exp"], int)
    assert payload["exp"] > payload["iat"]


def test_create_refresh_token_contains_expected_claims() -> None:
    service = JWTService()

    token = service.create_refresh_token(subject="user-123")
    payload = service.decode_token(token)

    assert payload["sub"] == "user-123"
    assert payload["type"] == TokenType.REFRESH.value
    assert "role" not in payload
    assert isinstance(payload["iat"], int)
    assert isinstance(payload["exp"], int)
    assert payload["exp"] > payload["iat"]


def test_verify_token_returns_true_for_valid_token() -> None:
    service = JWTService()
    token = service.create_access_token(subject="user-123", role=UserRole.USER.value)

    assert service.verify_token(token) is True


def test_decode_token_raises_for_expired_token() -> None:
    service = JWTService()

    now = datetime.now(UTC)
    payload = {
        "sub": "user-123",
        "type": TokenType.ACCESS.value,
        "role": UserRole.USER.value,
        "iat": int((now - timedelta(minutes=10)).timestamp()),
        "exp": int((now - timedelta(minutes=1)).timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(TokenExpiredException, match="expired"):
        service.decode_token(token)


def test_decode_token_raises_for_malformed_token() -> None:
    service = JWTService()

    with pytest.raises(InvalidTokenException, match="Invalid authentication token"):
        service.decode_token("this-is-not-a-jwt")


def test_decode_token_raises_for_invalid_signature() -> None:
    service = JWTService()

    token = jwt.encode(
        {
            "sub": "user-123",
            "type": TokenType.ACCESS.value,
            "role": UserRole.USER.value,
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        },
        "wrong-secret",
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(InvalidTokenException):
        service.decode_token(token)


def test_verify_token_returns_false_for_expired_token() -> None:
    service = JWTService()

    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": "user-123",
            "type": TokenType.REFRESH.value,
            "iat": int((now - timedelta(days=10)).timestamp()),
            "exp": int((now - timedelta(seconds=1)).timestamp()),
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )

    assert service.verify_token(token) is False


def test_verify_token_returns_false_for_malformed_token() -> None:
    service = JWTService()

    assert service.verify_token("malformed-token") is False
