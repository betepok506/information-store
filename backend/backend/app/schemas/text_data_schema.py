from uuid import UUID
from pydantic import Field
from typing import Optional, List
from sqlmodel import SQLModel
from backend.app.models.processed_urls_model import ProcessedUrlsBase
from backend.app.models.text_data_model import TextDataBase
from backend.app.schemas.text_vector_schema import TextVectorBase
from backend.app.utils.partial import optional



# class ITextDataRequest(TextDataBase, TextVectorBase):
#     url: str  # URL адресс откуда взят текст
#     source_name: str  # Имя источника
#     elastic_id: str = Field(..., exclude=True)


# class ITextDataCreate(TextDataBase):
#     processed_urls_id: UUID


# # class IListTextDataCreate(TextDataBase):
# #     items: ITextDataCreate
# # processed_urls_id: UUID


class IProcessedUrlsReadBasic(ProcessedUrlsBase):
    id: UUID


# class ITextDataReadNotVectors(TextDataBase):
#     id: UUID
#     processed_urls: IProcessedUrlsReadBasic | None = None


# class ITextDataRead(ITextDataReadNotVectors, TextVectorBase):
#     pass


# @optional()
# class ITextDataUpdateRequest(ITextDataRequest):
#     pass


# # All these fields are optional
# @optional()
# class ITextDataUpdate(ITextDataCreate):
#     _elastic_id: str

# Схемы запросов


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
    # pass
    text: str  # Текст записи
    elastic_id: str  # Индекс записи в Elastic Search
    processed_urls_id: UUID


@optional()
class ITextDataUpdate(ITextDataCreate):
    pass


# Схема ответов
class ITextDataReadBasic(TextDataBase):
    id: UUID
    text: str
    elastic_id: str
    url: str
    processed_urls_id: UUID
    # processed_urls: IProcessedUrlsReadBasic | None = None


class ITextDataReadFull(ITextDataReadBasic):
    vector: List[float]
