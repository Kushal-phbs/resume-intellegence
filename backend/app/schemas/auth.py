"""Authentication-related request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.enums import TokenType, UserRole


class RegisterRequest(BaseModel):
    """Payload for account registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """Payload for login requests."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshTokenRequest(BaseModel):
    """Payload for requesting a new access token from a refresh token."""

    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    """Standard JWT token response payload."""

    access_token: str = Field(min_length=1)
    refresh_token: str = Field(min_length=1)
    token_type: Literal["bearer"] = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload data model."""

    model_config = ConfigDict(extra="ignore")

    sub: str
    type: TokenType
    iat: int
    exp: int
    role: UserRole | None = None

    @model_validator(mode="after")
    def validate_timestamps(self) -> "TokenPayload":
        """Ensure token expiration is later than issued-at time."""
        if self.exp <= self.iat:
            raise ValueError("Token exp must be greater than iat")
        return self


class CurrentUserResponse(BaseModel):
    """Response model for the authenticated user profile endpoint."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
