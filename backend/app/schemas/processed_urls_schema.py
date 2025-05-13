from uuid import UUID

from pydantic import BaseModel
from sqlmodel import SQLModel

from app.models import ProcessedUrlsBase, SourceBase
from app.utils.partial import optional

__all__ = [
    "IProcessedUrlsCreate",
    "IProcessedUrlsUpdate",
    "ISourceReadBasic",
    "IProcessedUrlsReadBasic",
    "IPorcessedUrlsReadFull",
    "IProcessedUrlsResponse",
    "IProcessedUrlsRead",
]


class IProcessedUrlsCreate(ProcessedUrlsBase):
    source_id: UUID


# All these fields are optional
@optional()
class IProcessedUrlsUpdate(ProcessedUrlsBase):
    class Config:
        exclude_unset = True


class ISourceReadBasic(SourceBase):
    id: UUID


class IProcessedUrlsReadBasic(SQLModel):
    url: str
    hash: str


class IPorcessedUrlsReadFull(SQLModel):
    url: str
    hash: str
    source_name: str


class IProcessedUrlsResponse(BaseModel):
    id: UUID | int
    url: str
    source_name: str


class IProcessedUrlsRead(ProcessedUrlsBase):
    id: UUID
    source: ISourceReadBasic | None = None
