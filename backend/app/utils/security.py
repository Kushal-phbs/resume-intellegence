"""Shared security helper utilities.

These helpers centralize token claim validation to avoid duplicated parsing
logic across auth dependencies and services.
"""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from app.core.exceptions import InvalidTokenException
from app.enums import TokenType


def validate_token_type(payload: Mapping[str, Any], expected_type: TokenType) -> None:
    """Validate that a JWT payload has the expected token type.

    Args:
        payload: Decoded JWT payload.
        expected_type: Required token type.

    Raises:
        InvalidTokenException: If payload type is missing or does not match.
    """
    token_type = payload.get("type")
    if token_type != expected_type.value:
        raise InvalidTokenException(f"Invalid {expected_type.value} token type")


def extract_subject_uuid(payload: Mapping[str, Any]) -> UUID:
    """Extract and validate the UUID subject claim from a JWT payload.

    Args:
        payload: Decoded JWT payload.

    Returns:
        Parsed UUID from the ``sub`` claim.

    Raises:
        InvalidTokenException: If subject is missing or not a valid UUID.
    """
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise InvalidTokenException("Token subject is missing")

    try:
        return UUID(subject)
    except ValueError as exc:
        raise InvalidTokenException("Token subject is invalid") from exc
