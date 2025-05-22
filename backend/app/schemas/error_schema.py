# app/schemas/error.py

from typing import Any, Dict, Optional, List
from enum import Enum

from pydantic import BaseModel

__all__ = ["ErrorDetail", "ErrorCode", "IErrorResponseBase"]


class ErrorCode(str, Enum):
    # Общие ошибки
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    BAD_REQUEST = "BAD_REQUEST"


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class IErrorResponseBase(BaseModel):
    message: str
    error_code: ErrorCode
    details: Optional[List[ErrorDetail]] = None
    meta: Optional[Dict[str, Any]] = {}
