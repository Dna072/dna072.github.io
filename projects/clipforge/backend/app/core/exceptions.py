"""Domain-level exceptions mapped to HTTP responses in the API layer."""

from __future__ import annotations


class AppError(Exception):
    """Base class for expected, client-facing errors."""

    status_code: int = 400
    code: str = "app_error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.__name__
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class AuthError(AppError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"
