"""Authentication-related request/response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.enums import TokenType, UserRole


class RegisterRequest(BaseModel):
    """Payload for account registration."""

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """Payload for login requests."""

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class RefreshTokenRequest(BaseModel):
    """Payload for requesting a new access token from a refresh token."""

    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    """Standard JWT token response payload."""

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload data model."""

    model_config = ConfigDict(extra="ignore")

    sub: str
    type: TokenType
    iat: int
    exp: int
    role: UserRole | None = None
