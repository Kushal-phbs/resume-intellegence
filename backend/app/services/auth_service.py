"""Authentication business logic service."""

from __future__ import annotations

from uuid import UUID

from app.core.exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
)
from app.enums import TokenType, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.jwt_service import JWTService
from app.services.password_service import PasswordService
from app.utils.security import extract_subject_uuid, validate_token_type


class AuthService:
    """Orchestrate registration/login/refresh authentication use-cases."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_service: PasswordService,
        jwt_service: JWTService,
    ) -> None:
        self._user_repository = user_repository
        self._password_service = password_service
        self._jwt_service = jwt_service

    def _issue_tokens(self, user_id: UUID, role: str) -> TokenResponse:
        """Issue a fresh access and refresh token pair for a user.

        Args:
            user_id: User identifier to place in the JWT subject claim.
            role: User role to place in access token claims.

        Returns:
            A token response with access and refresh JWTs.
        """
        access_token = self._jwt_service.create_access_token(
            subject=str(user_id),
            role=role,
        )
        refresh_token = self._jwt_service.create_refresh_token(subject=str(user_id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def register(self, request: RegisterRequest) -> TokenResponse:
        """Register a new user and return generated JWTs.

        Args:
            request: Registration payload validated by Pydantic.

        Returns:
            Newly issued access and refresh token pair.

        Raises:
            UserAlreadyExistsException: If request email already exists.
        """
        if await self._user_repository.email_exists(request.email):
            raise UserAlreadyExistsException()

        hashed_password = self._password_service.hash_password(request.password)
        user = await self._user_repository.create_user(
            email=request.email,
            full_name=request.full_name,
            hashed_password=hashed_password,
            role=UserRole.USER.value,
        )

        return self._issue_tokens(user.id, user.role)

    async def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate a user with email/password and return JWTs.

        Args:
            request: Login payload validated by Pydantic.

        Returns:
            Newly issued access and refresh token pair.

        Raises:
            InvalidCredentialsException: If email is unknown or password mismatches.
        """
        user = await self._user_repository.get_by_email(request.email)
        if user is None:
            raise InvalidCredentialsException()

        if not self._password_service.verify_password(
            request.password, user.hashed_password
        ):
            raise InvalidCredentialsException()

        return self._issue_tokens(user.id, user.role)

    async def refresh(self, request: RefreshTokenRequest) -> TokenResponse:
        """Validate a refresh token and return a newly issued token pair.

        Args:
            request: Refresh token payload validated by Pydantic.

        Returns:
            Newly issued access and refresh token pair.

        Raises:
            InvalidTokenException: If refresh token claims are invalid.
            TokenExpiredException: Propagated from JWTService when expired.
            InvalidCredentialsException: If token user no longer exists.
        """
        payload = self._jwt_service.decode_token(request.refresh_token)

        validate_token_type(payload, TokenType.REFRESH)
        user_id = extract_subject_uuid(payload)

        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise InvalidCredentialsException()

        return self._issue_tokens(user.id, user.role)
