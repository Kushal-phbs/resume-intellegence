"""Password hashing service using pwdlib.

This service is intentionally isolated from frameworks and persistence so it can
be reused anywhere in the application that needs password hashing primitives.
"""

from __future__ import annotations

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError


class PasswordService:
    """Provide password hashing and verification primitives."""

    def __init__(self) -> None:
        self._password_hash = PasswordHash.recommended()

    def hash_password(self, password: str) -> str:
        """Return a secure hash for the provided plain text password."""
        return self._password_hash.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Return True when the plain password matches the stored hash."""
        try:
            return self._password_hash.verify(plain_password, hashed_password)
        except (UnknownHashError, ValueError):
            return False
