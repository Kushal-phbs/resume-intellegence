"""Dependency providers for authentication repository/services."""

from __future__ import annotations

from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
)
from app.db.dependency import get_db_session
from app.enums import TokenType, UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.jwt_service import JWTService
from app.services.password_service import PasswordService
from app.utils.security import extract_subject_uuid, validate_token_type

_bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repository(
    db_session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    """Create a user repository bound to the provided async session."""
    return UserRepository(db_session)


def get_password_service() -> PasswordService:
    """Create and return a PasswordService instance."""
    return PasswordService()


def get_jwt_service() -> JWTService:
    """Create and return a JWTService instance."""
    return JWTService()


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    password_service: PasswordService = Depends(get_password_service),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> AuthService:
    """Create and return an AuthService instance."""
    return AuthService(user_repository, password_service, jwt_service)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
    user_repository: UserRepository = Depends(get_user_repository),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> User:
    """Resolve the authenticated user from a Bearer token.

    Args:
        credentials: Parsed HTTP Authorization header credentials.
        user_repository: Repository used to load the current user.
        jwt_service: Service used to decode and validate JWTs.

    Returns:
        Authenticated user ORM model.

    Raises:
        AuthenticationException: If credentials are missing or user is gone.
        InvalidTokenException: If token claims are invalid.
        TokenExpiredException: Propagated from JWTService when expired.
    """
    if credentials is None or not credentials.credentials:
        raise AuthenticationException()

    payload = jwt_service.decode_token(credentials.credentials)

    validate_token_type(payload, TokenType.ACCESS)
    user_id = extract_subject_uuid(payload)

    user = await user_repository.get_by_id(user_id)
    if user is None:
        raise AuthenticationException("Authenticated user no longer exists")

    request.state.user_id = str(user.id)
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the current user has admin privileges.

    Args:
        current_user: Already authenticated user.

    Returns:
        The same authenticated user when role is admin.

    Raises:
        AuthorizationException: If the user is not an admin.
    """
    if current_user.role != UserRole.ADMIN.value:
        raise AuthorizationException("Admin access required")
    return current_user
