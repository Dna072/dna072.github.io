"""Domain-level exceptions mapped to HTTP responses by handlers in main."""

from __future__ import annotations


class AppError(Exception):
    """Base class for application errors carrying an HTTP status code."""

    status_code: int = 400
    code: str = "app_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class AuthenticationError(AppError):
    status_code = 401
    code = "authentication_error"


class PermissionError_(AppError):
    status_code = 403
    code = "permission_denied"


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"
