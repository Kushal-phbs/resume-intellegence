"""Authentication business logic service."""

from __future__ import annotations

from app.core.exceptions import InvalidCredentialsException, UserAlreadyExistsException
from app.enums import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.jwt_service import JWTService
from app.services.password_service import PasswordService


class AuthService:
    """Orchestrate registration and login authentication use-cases."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_service: PasswordService,
        jwt_service: JWTService,
    ) -> None:
        self._user_repository = user_repository
        self._password_service = password_service
        self._jwt_service = jwt_service

    async def register(self, request: RegisterRequest) -> TokenResponse:
        """Register a new user and return generated JWTs."""
        if await self._user_repository.email_exists(request.email):
            raise UserAlreadyExistsException()

        hashed_password = self._password_service.hash_password(request.password)
        user = await self._user_repository.create_user(
            email=request.email,
            full_name=request.full_name,
            hashed_password=hashed_password,
            role=UserRole.USER.value,
        )

        access_token = self._jwt_service.create_access_token(
            subject=str(user.id),
            role=user.role,
        )
        refresh_token = self._jwt_service.create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate a user with email/password and return JWTs."""
        user = await self._user_repository.get_by_email(request.email)
        if user is None:
            raise InvalidCredentialsException()

        if not self._password_service.verify_password(
            request.password, user.hashed_password
        ):
            raise InvalidCredentialsException()

        access_token = self._jwt_service.create_access_token(
            subject=str(user.id),
            role=user.role,
        )
        refresh_token = self._jwt_service.create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
