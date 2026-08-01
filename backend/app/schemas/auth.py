"""Authentication-related request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.enums import TokenType, UserRole


class RegisterRequest(BaseModel):
    """Payload for account registration."""

    email: EmailStr = Field(description="User email address used for login.")
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Plaintext password used to create the account.",
        examples=["Str0ngPassword!"],
    )
    full_name: str = Field(
        min_length=1,
        max_length=255,
        description="Display name for the user profile.",
        examples=["Alex Morgan"],
    )


class LoginRequest(BaseModel):
    """Payload for login requests."""

    email: EmailStr = Field(description="Registered account email address.")
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Account password.",
    )


class RefreshTokenRequest(BaseModel):
    """Payload for requesting a new access token from a refresh token."""

    refresh_token: str = Field(
        min_length=1,
        description="Valid refresh token issued by the login or refresh endpoint.",
    )


class TokenResponse(BaseModel):
    """Standard JWT token response payload."""

    access_token: str = Field(
        min_length=1,
        description="JWT access token used to authorize API requests.",
    )
    refresh_token: str = Field(
        min_length=1,
        description="JWT refresh token used to request new token pairs.",
    )
    token_type: Literal["bearer"] = Field(
        default="bearer",
        description="Token type for Authorization header usage.",
    )


class TokenPayload(BaseModel):
    """Decoded JWT payload data model."""

    model_config = ConfigDict(extra="ignore")

    sub: str = Field(description="Subject claim containing the user identifier.")
    type: TokenType = Field(description="Token type claim (access or refresh).")
    iat: int = Field(description="Issued-at timestamp in Unix epoch seconds.")
    exp: int = Field(description="Expiration timestamp in Unix epoch seconds.")
    role: UserRole | None = Field(
        default=None,
        description="Optional role claim embedded in access tokens.",
    )

    @model_validator(mode="after")
    def validate_timestamps(self) -> "TokenPayload":
        """Ensure token expiration is later than issued-at time."""
        if self.exp <= self.iat:
            raise ValueError("Token exp must be greater than iat")
        return self


class CurrentUserResponse(BaseModel):
    """Response model for the authenticated user profile endpoint."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="User identifier.")
    email: str = Field(description="User email address.")
    full_name: str = Field(description="User display name.")
    role: UserRole = Field(description="Current authorization role.")
    is_active: bool = Field(description="Whether the account is active.")
    created_at: datetime = Field(description="Account creation timestamp.")
    updated_at: datetime = Field(description="Last account update timestamp.")
