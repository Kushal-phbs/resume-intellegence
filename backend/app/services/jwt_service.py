"""Reusable JWT primitives for authentication workflows.

This service is framework-agnostic and storage-agnostic by design: it only
creates and validates JWTs using project settings.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.config.settings import settings
from app.core.exceptions import InvalidTokenException, TokenExpiredException
from app.enums import TokenType


class JWTService:
    """Create and validate access/refresh JWTs."""

    def create_access_token(self, subject: str, role: str) -> str:
        """Create a signed access token for a subject and role.

        Args:
            subject: User identifier for the JWT subject claim.
            role: User role for authorization decisions.

        Returns:
            Encoded JWT string.
        """
        now = datetime.now(UTC)
        exp = now + timedelta(minutes=settings.access_token_expire_minutes)
        payload: dict[str, Any] = {
            "sub": subject,
            "role": role,
            "type": TokenType.ACCESS.value,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return jwt.encode(
            payload,
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )

    def create_refresh_token(self, subject: str) -> str:
        """Create a signed refresh token for a subject.

        Args:
            subject: User identifier for the JWT subject claim.

        Returns:
            Encoded JWT string.
        """
        now = datetime.now(UTC)
        exp = now + timedelta(days=settings.refresh_token_expire_days)
        payload: dict[str, Any] = {
            "sub": subject,
            "type": TokenType.REFRESH.value,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return jwt.encode(
            payload,
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate a token, returning its payload.

        Args:
            token: Encoded JWT string.

        Returns:
            Decoded payload dictionary.

        Raises:
            TokenExpiredException: If token expiration has passed.
            InvalidTokenException: If token is malformed, invalid, or fails
                signature/claims verification.
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except ExpiredSignatureError as exc:
            raise TokenExpiredException() from exc
        except InvalidTokenError as exc:
            raise InvalidTokenException() from exc

        if not isinstance(payload, dict):
            raise InvalidTokenException("Token payload must be a JSON object.")

        return payload

    def verify_token(self, token: str) -> bool:
        """Return True if token is valid and not expired.

        Args:
            token: Encoded JWT string.

        Returns:
            ``True`` when token is valid and unexpired, otherwise ``False``.
        """
        try:
            self.decode_token(token)
        except (TokenExpiredException, InvalidTokenException):
            return False
        return True
