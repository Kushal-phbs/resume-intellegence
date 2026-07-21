from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    UserAlreadyExistsException,
)
from app.enums import TokenType, UserRole
from app.schemas.auth import LoginRequest, RefreshTokenRequest, RegisterRequest
from app.services.auth_service import AuthService


def _build_service() -> tuple[AuthService, AsyncMock, MagicMock, MagicMock]:
    user_repository = AsyncMock()
    password_service = MagicMock()
    jwt_service = MagicMock()
    service = AuthService(user_repository, password_service, jwt_service)
    return service, user_repository, password_service, jwt_service


def test_register_successful_registration_returns_tokens() -> None:
    service, user_repository, password_service, jwt_service = _build_service()
    request = RegisterRequest(
        email="john@example.com",
        password="StrongPass123!",
        full_name="John Doe",
    )
    created_user = SimpleNamespace(id=uuid4(), role=UserRole.USER.value)

    user_repository.email_exists.return_value = False
    password_service.hash_password.return_value = "hashed-password"
    user_repository.create_user.return_value = created_user
    jwt_service.create_access_token.return_value = "access-token"
    jwt_service.create_refresh_token.return_value = "refresh-token"

    response = asyncio.run(service.register(request))

    assert response.access_token == "access-token"
    assert response.refresh_token == "refresh-token"
    user_repository.email_exists.assert_awaited_once_with("john@example.com")
    password_service.hash_password.assert_called_once_with("StrongPass123!")
    user_repository.create_user.assert_awaited_once_with(
        email="john@example.com",
        full_name="John Doe",
        hashed_password="hashed-password",
        role=UserRole.USER.value,
    )
    jwt_service.create_access_token.assert_called_once_with(
        subject=str(created_user.id),
        role=UserRole.USER.value,
    )
    jwt_service.create_refresh_token.assert_called_once_with(
        subject=str(created_user.id)
    )


def test_register_duplicate_email_raises_exception() -> None:
    service, user_repository, password_service, jwt_service = _build_service()
    request = RegisterRequest(
        email="john@example.com",
        password="StrongPass123!",
        full_name="John Doe",
    )
    user_repository.email_exists.return_value = True

    with pytest.raises(UserAlreadyExistsException):
        asyncio.run(service.register(request))

    password_service.hash_password.assert_not_called()
    user_repository.create_user.assert_not_called()
    jwt_service.create_access_token.assert_not_called()
    jwt_service.create_refresh_token.assert_not_called()


def test_register_hashes_password_before_creating_user() -> None:
    service, user_repository, password_service, jwt_service = _build_service()
    request = RegisterRequest(
        email="john@example.com",
        password="StrongPass123!",
        full_name="John Doe",
    )
    created_user = SimpleNamespace(id=uuid4(), role=UserRole.USER.value)

    user_repository.email_exists.return_value = False
    password_service.hash_password.return_value = "hashed-password"
    user_repository.create_user.return_value = created_user
    jwt_service.create_access_token.return_value = "access-token"
    jwt_service.create_refresh_token.return_value = "refresh-token"

    asyncio.run(service.register(request))

    password_service.hash_password.assert_called_once_with(request.password)
    create_kwargs = user_repository.create_user.await_args.kwargs
    assert create_kwargs["hashed_password"] == "hashed-password"


def test_register_generates_access_and_refresh_tokens() -> None:
    service, user_repository, password_service, jwt_service = _build_service()
    request = RegisterRequest(
        email="john@example.com",
        password="StrongPass123!",
        full_name="John Doe",
    )
    created_user = SimpleNamespace(id=uuid4(), role=UserRole.USER.value)

    user_repository.email_exists.return_value = False
    password_service.hash_password.return_value = "hashed-password"
    user_repository.create_user.return_value = created_user
    jwt_service.create_access_token.return_value = "access-token"
    jwt_service.create_refresh_token.return_value = "refresh-token"

    asyncio.run(service.register(request))

    jwt_service.create_access_token.assert_called_once()
    jwt_service.create_refresh_token.assert_called_once()


def test_login_successful_returns_tokens() -> None:
    service, user_repository, password_service, jwt_service = _build_service()
    request = LoginRequest(email="john@example.com", password="StrongPass123!")
    existing_user = SimpleNamespace(
        id=uuid4(),
        hashed_password="hashed-password",
        role=UserRole.USER.value,
    )

    user_repository.get_by_email.return_value = existing_user
    password_service.verify_password.return_value = True
    jwt_service.create_access_token.return_value = "access-token"
    jwt_service.create_refresh_token.return_value = "refresh-token"

    response = asyncio.run(service.login(request))

    assert response.access_token == "access-token"
    assert response.refresh_token == "refresh-token"
    user_repository.get_by_email.assert_awaited_once_with("john@example.com")
    password_service.verify_password.assert_called_once_with(
        "StrongPass123!", "hashed-password"
    )
    jwt_service.create_access_token.assert_called_once_with(
        subject=str(existing_user.id),
        role=UserRole.USER.value,
    )
    jwt_service.create_refresh_token.assert_called_once_with(
        subject=str(existing_user.id)
    )


def test_login_unknown_email_raises_invalid_credentials() -> None:
    service, user_repository, password_service, jwt_service = _build_service()
    request = LoginRequest(email="john@example.com", password="StrongPass123!")
    user_repository.get_by_email.return_value = None

    with pytest.raises(InvalidCredentialsException):
        asyncio.run(service.login(request))

    password_service.verify_password.assert_not_called()
    jwt_service.create_access_token.assert_not_called()
    jwt_service.create_refresh_token.assert_not_called()


def test_login_wrong_password_raises_invalid_credentials() -> None:
    service, user_repository, password_service, jwt_service = _build_service()
    request = LoginRequest(email="john@example.com", password="WrongPassword123!")
    existing_user = SimpleNamespace(
        id=uuid4(),
        hashed_password="hashed-password",
        role=UserRole.USER.value,
    )
    user_repository.get_by_email.return_value = existing_user
    password_service.verify_password.return_value = False

    with pytest.raises(InvalidCredentialsException):
        asyncio.run(service.login(request))

    password_service.verify_password.assert_called_once_with(
        "WrongPassword123!", "hashed-password"
    )
    jwt_service.create_access_token.assert_not_called()
    jwt_service.create_refresh_token.assert_not_called()


def test_refresh_successful_returns_tokens() -> None:
    service, user_repository, password_service, jwt_service = _build_service()
    request = RefreshTokenRequest(refresh_token="refresh-token")
    user_id = uuid4()
    existing_user = SimpleNamespace(id=user_id, role=UserRole.USER.value)

    jwt_service.decode_token.return_value = {
        "sub": str(user_id),
        "type": TokenType.REFRESH.value,
    }
    user_repository.get_by_id.return_value = existing_user
    jwt_service.create_access_token.return_value = "new-access"
    jwt_service.create_refresh_token.return_value = "new-refresh"

    response = asyncio.run(service.refresh(request))

    assert response.access_token == "new-access"
    assert response.refresh_token == "new-refresh"
    jwt_service.decode_token.assert_called_once_with("refresh-token")
    user_repository.get_by_id.assert_awaited_once_with(user_id)
    jwt_service.create_access_token.assert_called_once_with(
        subject=str(user_id),
        role=UserRole.USER.value,
    )
    jwt_service.create_refresh_token.assert_called_once_with(subject=str(user_id))
    password_service.hash_password.assert_not_called()
    password_service.verify_password.assert_not_called()


def test_refresh_invalid_token_type_raises_invalid_token() -> None:
    service, user_repository, _password_service, jwt_service = _build_service()
    request = RefreshTokenRequest(refresh_token="refresh-token")

    jwt_service.decode_token.return_value = {
        "sub": str(uuid4()),
        "type": TokenType.ACCESS.value,
    }

    with pytest.raises(InvalidTokenException):
        asyncio.run(service.refresh(request))

    user_repository.get_by_id.assert_not_called()


def test_refresh_unknown_user_raises_invalid_credentials() -> None:
    service, user_repository, _password_service, jwt_service = _build_service()
    user_id = uuid4()
    request = RefreshTokenRequest(refresh_token="refresh-token")

    jwt_service.decode_token.return_value = {
        "sub": str(user_id),
        "type": TokenType.REFRESH.value,
    }
    user_repository.get_by_id.return_value = None

    with pytest.raises(InvalidCredentialsException):
        asyncio.run(service.refresh(request))

    user_repository.get_by_id.assert_awaited_once_with(user_id)


def test_refresh_invalid_subject_raises_invalid_token() -> None:
    service, user_repository, _password_service, jwt_service = _build_service()
    request = RefreshTokenRequest(refresh_token="refresh-token")

    jwt_service.decode_token.return_value = {
        "sub": "not-a-uuid",
        "type": TokenType.REFRESH.value,
    }

    with pytest.raises(InvalidTokenException):
        asyncio.run(service.refresh(request))

    user_repository.get_by_id.assert_not_called()
