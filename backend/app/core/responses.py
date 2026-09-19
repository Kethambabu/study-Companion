from datetime import UTC, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

DataType = TypeVar("DataType")


class ErrorDetail(BaseModel):
    field: str | None = None
    issue: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ResponseMeta(BaseModel):
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    request_id: str | None = None


class ApiResponse(BaseModel, Generic[DataType]):
    success: bool
    data: DataType | None = None
    error: ErrorBody | None = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)

    @classmethod
    def ok(cls, data: DataType, request_id: str | None = None) -> "ApiResponse[DataType]":
        return cls(
            success=True,
            data=data,
            error=None,
            meta=ResponseMeta(request_id=request_id),
        )

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
        details: list[ErrorDetail] | None = None,
        request_id: str | None = None,
    ) -> "ApiResponse[None]":
        return cls(
            success=False,
            data=None,
            error=ErrorBody(
                code=code,
                message=message,
                details=details or [],
            ),
            meta=ResponseMeta(request_id=request_id),
        )
