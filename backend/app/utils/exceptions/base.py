# app/utils/exceptions.py

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.routing import APIRoute

from app.schemas import IErrorResponseBase, ErrorCode

__all__ = ["APIException", "api_exception_handler", "add_exception_handlers"]


class APIException(HTTPException):
    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        details: list | None = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.message = message
        self.details = details


def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content=IErrorResponseBase(
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details,
        ).model_dump(),
    )


def add_exception_handlers(app: APIRoute):
    app.add_exception_handler(APIException, api_exception_handler)
