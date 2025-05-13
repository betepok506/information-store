from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)


class ContentNoChangeException(HTTPException):
    def __init__(
        self,
        detail: Any = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers,
        )


class IdNotFoundException(HTTPException, Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
        id: Optional[Union[UUID, str]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        if id:
            super().__init__(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unable to find the {model.__name__} with id {id}.",
                headers=headers,
            )
            return

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} id not found.",
            headers=headers,
        )


class SourceNotFoundException(HTTPException, Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
        source: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        if source:
            super().__init__(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unable to find the {model.__name__} source {source}.",
                headers=headers,
            )
        else:
            super().__init__(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} source not found.",
                headers=headers,
            )


class ProcessedUrlNotFoundException(HTTPException, Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
        url: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        if url:
            super().__init__(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unable to find the {model.__name__} url {url}.",
                headers=headers,
            )
        else:
            super().__init__(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} url not found.",
                headers=headers,
            )


class SourceExistException(HTTPException, Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
        source: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        if source:
            super().__init__(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"The {model.__name__} source {source} already exists.",
                headers=headers,
            )
            return

        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"The {model.__name__} source already exists.",
            headers=headers,
        )


class UrlValidationError(HTTPException, Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
        name: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        if name:
            super().__init__(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The transmitted URL is not the source address.",
                headers=headers,
            )
            return

        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The transmitted URL is not the source address.",
            headers=headers,
        )


__all__ = [
    "ContentNoChangeException",
    "IdNotFoundException",
    "SourceNotFoundException",
    "ProcessedUrlNotFoundException",
    "UrlValidationError",
    "SourceExistException",
]
