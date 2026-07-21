"""Dependency providers for authentication repository/services."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.jwt_service import JWTService
from app.services.password_service import PasswordService


def get_user_repository(db_session: AsyncSession) -> UserRepository:
    """Create a user repository bound to the provided async session."""
    return UserRepository(db_session)


def get_password_service() -> PasswordService:
    """Create and return a PasswordService instance."""
    return PasswordService()


def get_jwt_service() -> JWTService:
    """Create and return a JWTService instance."""
    return JWTService()


def get_auth_service(
    user_repository: UserRepository,
    password_service: PasswordService,
    jwt_service: JWTService,
) -> AuthService:
    """Create and return an AuthService instance."""
    return AuthService(user_repository, password_service, jwt_service)
