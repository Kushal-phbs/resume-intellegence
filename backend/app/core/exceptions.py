"""Application-specific exception hierarchy.

Defines a small set of reusable exceptions that carry an HTTP-like status_code
and a human-readable message. These are intended for use in application code
and exception handlers that translate exceptions to HTTP responses.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppException(Exception):
    """Base application exception carrying a message and HTTP-style status_code.

    Attributes:
        message: Human readable error message.
        status_code: HTTP-style status code representing the error class.
    """

    message: str
    status_code: int = 500

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


class ValidationException(AppException):
    """Raised for request or data validation errors (client-side)."""

    def __init__(
        self, message: str = "Validation failed", status_code: int = 400
    ) -> None:
        super().__init__(message=message, status_code=status_code)


class ResourceNotFoundException(AppException):
    """Raised when a requested resource cannot be found."""

    def __init__(
        self, message: str = "Resource not found", status_code: int = 404
    ) -> None:
        super().__init__(message=message, status_code=status_code)


class AuthenticationException(AppException):
    """Raised when authentication (identity) fails or is missing."""

    def __init__(
        self, message: str = "Authentication required", status_code: int = 401
    ) -> None:
        super().__init__(message=message, status_code=status_code)


class AuthorizationException(AppException):
    """Raised when an authenticated principal is not permitted to perform an action."""

    def __init__(self, message: str = "Not authorized", status_code: int = 403) -> None:
        super().__init__(message=message, status_code=status_code)


class ExternalServiceException(AppException):
    """Raised for failures when calling external services (upstream errors)."""

    def __init__(
        self, message: str = "External service error", status_code: int = 502
    ) -> None:
        super().__init__(message=message, status_code=status_code)
