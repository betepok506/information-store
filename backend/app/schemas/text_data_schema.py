from typing import List
from uuid import UUID

from sqlmodel import SQLModel

from app.models import ProcessedUrlsBase
from app.utils.partial import optional

__all__ = [
    "ITextDataCreateRequest",
    "ITextDataUpdateRequest",
    "ITextDataCreate",
    "ITextDataUpdate",
    "ITextDataReadBasic",
    "ITextDataReadFull",
]


class IProcessedUrlsReadBasic(ProcessedUrlsBase):
    id: UUID


class ITextDataCreateRequest(SQLModel):
    text: str  # Текст записи
    url: str  # URL адрес откуда взят текст
    source_name: str  # Имя источника
    vector: List[float]


@optional()
class ITextDataUpdateRequest(ITextDataCreateRequest):
    pass


# Схемы создания записей в БД
class ITextDataCreate(SQLModel):
    text: str  # Текст записи
    elastic_id: str  # Индекс записи в Elastic Search
    processed_urls_id: UUID


@optional()
class ITextDataUpdate(ITextDataCreate):
    pass


# Схема ответов
class ITextDataReadBasic(SQLModel):
    id: UUID
    text: str
    elastic_id: str
    url: str
    # processed_urls_id: UUID

    # processed_urls: IProcessedUrlsReadBasic | None = None


class ITextDataReadFull(ITextDataReadBasic):
    vector: List[float]
