from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.logging import get_logger
from app.core.responses import ApiResponse, ErrorDetail

logger = get_logger("exceptions")


class AppException(Exception):
    """Base class for all domain and application exceptions."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: list[ErrorDetail] | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class EntityNotFoundError(AppException):
    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            code="ENTITY_NOT_FOUND",
            message=f"{entity_name} with id '{entity_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UnauthorizedAccessError(AppException):
    def __init__(self, message: str = "Authentication required or credentials invalid."):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class TenantAccessDeniedError(AppException):
    def __init__(self, message: str = "Access denied for requested space context."):
        super().__init__(
            code="TENANT_ACCESS_DENIED",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class AIProviderError(AppException):
    def __init__(self, provider: str, message: str, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(
            code="AI_PROVIDER_ERROR",
            message=f"AI provider '{provider}' failed: {message}",
            status_code=status_code,
        )


class RateLimitExceededError(AppException):
    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class LLMGenerationError(AppException):
    def __init__(self, message: str = "Failed to generate valid structured LLM response."):
        super().__init__(
            code="LLM_GENERATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class DuplicateSubmissionError(AppException):
    def __init__(self, message: str = "Answer has already been submitted for this question attempt."):
        super().__init__(
            code="DUPLICATE_SUBMISSION",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "Application exception occurred",
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        request_id=request_id,
    )
    response_content = ApiResponse.fail(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        request_id=request_id,
    ).model_dump()
    return JSONResponse(status_code=exc.status_code, content=response_content)


async def validation_exception_handler(
    request: Request, exc: PydanticValidationError | RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    details = [
        ErrorDetail(
            field=".".join(str(loc) for loc in err.get("loc", [])),
            issue=err.get("msg", "Invalid value"),
        )
        for err in exc.errors()
    ]
    logger.info(
        "Request validation error",
        error_count=len(details),
        request_id=request_id,
    )
    response_content = ApiResponse.fail(
        code="VALIDATION_ERROR",
        message="Request payload validation failed.",
        details=details,
        request_id=request_id,
    ).model_dump()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=response_content
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import traceback
    print("UNHANDLED EXCEPTION:", traceback.format_exc(), flush=True)
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        "Unhandled server error",
        error=str(exc),
        exc_info=True,
        request_id=request_id,
    )
    response_content = ApiResponse.fail(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal server error occurred.",
        request_id=request_id,
    ).model_dump()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response_content
    )
