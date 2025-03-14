from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel
from typing import Optional
from backend.app.models.base_uuid_model import BaseUUIDModel
from backend.app.models.source_model import Source


class ProcessedUrlsBase(SQLModel):
    url: str = Field(index=True)
    hash: str = Field(index=True)


class ProcessedUrls(BaseUUIDModel, ProcessedUrlsBase, table=True):
    source_id: UUID | None = Field(default=None, foreign_key="Source.id")
    source: Source | None = Relationship(  # noqa: F821
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "ProcessedUrls.source_id==Source.id",
        },
        back_populates="processed_urls",
    )
    
    text_data: Optional["TextData"] | None = Relationship(  # noqa: F821
        back_populates="processed_urls",
    )
    
