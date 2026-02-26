import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.schemas.error import ErrorCode, ErrorResponse

logger = logging.getLogger(__name__)


def resolve_error_code(status_code: int) -> ErrorCode:
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


def _default_message_for_status(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "Request failed"


def _error_payload(status_code: int, message: str, details: Any = None) -> dict[str, Any]:
    payload = ErrorResponse(
        code=resolve_error_code(status_code),
        message=message,
        details=details,
    )
    return payload.model_dump(mode="json")


async def handle_http_exception(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
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
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            status_code=422,
            message="Request validation failed",
            details=exc.errors(),
        ),
    )


async def handle_unexpected_exception(_request: Request, exc: Exception) -> JSONResponse:
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
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_exception)
    app.add_exception_handler(Exception, handle_unexpected_exception)
