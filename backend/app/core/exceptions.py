"""Domain exceptions and shared helpers for service-layer error handling.

Route/API layers and FastAPI deps may still raise HTTPException at the HTTP
boundary. Business logic should raise AppError subclasses; handlers in main.py
map them to the same JSON shape FastAPI uses for HTTPException: {"detail": ...}.
"""

from __future__ import annotations

from typing import TypeVar

from fastapi import status

T = TypeVar("T")


class AppError(Exception):
    """Base application error with an HTTP status and response detail."""

    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail: str | dict = "Bad request"):
        self.detail = detail
        super().__init__(detail if isinstance(detail, str) else str(detail))


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, detail: str | dict = "Not found"):
        super().__init__(detail)


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, detail: str | dict = "Conflict"):
        super().__init__(detail)


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN

    def __init__(self, detail: str | dict = "Forbidden"):
        super().__init__(detail)


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, detail: str | dict = "Unauthorized"):
        super().__init__(detail)


class GoneError(AppError):
    """The resource existed but was deliberately turned off (e.g. a revoked share link)."""

    status_code = status.HTTP_410_GONE

    def __init__(self, detail: str | dict = "Gone"):
        super().__init__(detail)


class PreconditionFailedError(AppError):
    """An `If-Match` revision no longer matches (someone saved in between)."""

    status_code = status.HTTP_412_PRECONDITION_FAILED

    def __init__(self, detail: str | dict = "Precondition failed"):
        super().__init__(detail)


class PreconditionRequiredError(AppError):
    status_code = status.HTTP_428_PRECONDITION_REQUIRED

    def __init__(self, detail: str | dict = "Precondition required"):
        super().__init__(detail)


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail: str | dict = "Bad request"):
        super().__init__(detail)


class ServiceUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    def __init__(self, detail: str | dict = "Service unavailable"):
        super().__init__(detail)


class BadGatewayError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY

    def __init__(self, detail: str | dict = "Bad gateway"):
        super().__init__(detail)


class TooManyRequestsError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS

    def __init__(self, detail: str | dict = "Too many requests"):
        super().__init__(detail)


class PayloadTooLargeError(AppError):
    status_code = status.HTTP_413_CONTENT_TOO_LARGE

    def __init__(self, detail: str | dict = "Payload too large"):
        super().__init__(detail)


class UnprocessableError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT

    def __init__(self, detail: str | dict = "Unprocessable entity"):
        super().__init__(detail)


def get_or_404(entity: T | None, detail: str = "Not found") -> T:
    """Return entity or raise NotFoundError — replaces the repeated get→None→raise pattern."""
    if entity is None:
        raise NotFoundError(detail)
    return entity
