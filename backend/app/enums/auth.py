"""Authentication domain enums."""

from enum import StrEnum


class UserRole(StrEnum):
    """Supported user roles."""

    USER = "user"
    ADMIN = "admin"


class TokenType(StrEnum):
    """Supported JWT token kinds."""

    ACCESS = "access"
    REFRESH = "refresh"
