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


@router.post("/login", response_model=TokenResponse)
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


@router.post("/refresh", response_model=TokenResponse)
async def refresh_endpoint(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Issue a fresh token pair from a valid refresh token."""
    return await auth_service.refresh(request)
