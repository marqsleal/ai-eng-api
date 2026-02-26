import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.schemas.error import ErrorCode, ErrorResponse

logger = logging.getLogger(__name__)


def _default_message_for_status(status_code: int) -> str:
    """Return an HTTP reason phrase for a status code, with a safe fallback."""
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "Request failed"


def _normalize_validation_details(details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize FastAPI validation errors into JSON-safe details.

    FastAPI/Pydantic validation errors encode `loc` as tuples. Our error schema
    enforces `details` as `JsonValue`, which does not accept tuples, so this helper
    converts only tuple `loc` values to lists while preserving the original shape.
    """
    normalized: list[dict[str, Any]] = []
    for item in details:
        normalized_item = dict(item)
        loc_value = normalized_item.get("loc")
        if isinstance(loc_value, tuple):
            normalized_item["loc"] = list(loc_value)
        normalized.append(normalized_item)
    return normalized


def _error_payload(status_code: int, message: str, details: Any = None) -> dict[str, Any]:
    """Build a validated, JSON-serializable error payload for HTTP responses."""
    payload = ErrorResponse(
        code=resolve_error_code(status_code),
        message=message,
        details=details,
    )
    return payload.model_dump(mode="json")


def resolve_error_code(status_code: int) -> ErrorCode:
    """Resolve an HTTP status code into the API's typed `ErrorCode` enum."""
    match status_code:
        case 400:
            return ErrorCode.BAD_REQUEST
        case 401:
            return ErrorCode.UNAUTHORIZED
        case 403:
            return ErrorCode.FORBIDDEN
        case 404:
            return ErrorCode.NOT_FOUND
        case 405:
            return ErrorCode.METHOD_NOT_ALLOWED
        case 409:
            return ErrorCode.CONFLICT
        case 422:
            return ErrorCode.VALIDATION_ERROR
        case 429:
            return ErrorCode.TOO_MANY_REQUESTS
        case 500:
            return ErrorCode.INTERNAL_ERROR
        case 503:
            return ErrorCode.SERVICE_UNAVAILABLE
        case _:
            return ErrorCode.ERROR


def error_responses(*status_codes: int) -> dict[int, dict[str, Any]]:
    """Generate reusable OpenAPI response docs for standardized error payloads."""
    return {
        status_code: {
            "model": ErrorResponse,
            "description": _default_message_for_status(status_code),
        }
        for status_code in status_codes
    }


async def handle_http_exception(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle framework/application HTTP exceptions using the standard error contract."""
    detail = exc.detail
    message = detail if isinstance(detail, str) else _default_message_for_status(exc.status_code)
    details = None if isinstance(detail, str) else detail

    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc.status_code, message=message, details=details),
    )


async def handle_validation_exception(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors and return typed, JSON-safe details."""
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            status_code=422,
            message="Request validation failed",
            details=_normalize_validation_details(exc.errors()),
        ),
    )


async def handle_unexpected_exception(_request: Request, exc: Exception) -> JSONResponse:
    """Handle unanticipated exceptions with a generic 500 contract and error logging."""
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=_error_payload(
            status_code=500,
            message=_default_message_for_status(500),
            details=None,
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers that enforce the API error contract."""
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_exception)
    app.add_exception_handler(Exception, handle_unexpected_exception)
