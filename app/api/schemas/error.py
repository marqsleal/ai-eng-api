from enum import Enum

from pydantic import BaseModel, ConfigDict, JsonValue


class ErrorCode(Enum):
    BAD_REQUEST = "bad_request"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    CONFLICT = "conflict"
    VALIDATION_ERROR = "validation_error"
    TOO_MANY_REQUESTS = "too_many_requests"
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    ERROR = "error"


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ErrorCode
    message: str
    details: JsonValue | None = None
