from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.config import settings
from app.dependencies.auth import get_auth_service
from app.dependencies.rate_limit import limit
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register User",
    description="Create a new user account and issue access and refresh tokens.",
    responses={
        201: {"description": "User created and token pair issued."},
        400: {"description": "Invalid registration payload."},
        409: {"description": "User already exists."},
        429: {"description": "Register rate limit exceeded."},
    },
)
async def register_endpoint(
    request: RegisterRequest,
    _: None = Depends(
        limit(
            bucket="auth_register",
            requests=settings.rate_limit_register_requests,
        )
    ),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Register a user and return access/refresh JWT tokens."""
    return await auth_service.register(request)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login User",
    description="Authenticate credentials and issue access and refresh tokens.",
    responses={
        200: {"description": "Authentication successful; token pair issued."},
        401: {"description": "Invalid credentials."},
        429: {"description": "Login rate limit exceeded."},
    },
)
async def login_endpoint(
    request: LoginRequest,
    _: None = Depends(
        limit(
            bucket="auth_login",
            requests=settings.rate_limit_login_requests,
        )
    ),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate a user and return access/refresh JWT tokens."""
    return await auth_service.login(request)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Tokens",
    description="Exchange a valid refresh token for a new access and refresh pair.",
    responses={
        200: {"description": "Token pair refreshed."},
        401: {"description": "Invalid or expired refresh token."},
    },
)
async def refresh_endpoint(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Issue a fresh token pair from a valid refresh token."""
    return await auth_service.refresh(request)
