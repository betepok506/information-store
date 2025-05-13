from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from .base_uuid_model import BaseUUIDModel

if TYPE_CHECKING:
    from app.models import Source, TextData

__all__ = ["ProcessedUrlsBase", "ProcessedUrls"]


class ProcessedUrlsBase(BaseUUIDModel):
    url: str = Field(index=True)
    hash: str = Field(index=True)


class ProcessedUrls(ProcessedUrlsBase, table=True):
    # __tablename__ = "processed_urls"

    source_id: UUID | None = Field(default=None, foreign_key="Source.id")
    source: Optional["Source"] | None = Relationship(  # noqa: F821
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "ProcessedUrls.source_id==Source.id",
        },
        back_populates="processed_urls",
    )

    text_data: Optional["TextData"] | None = Relationship(  # noqa: F821
        back_populates="processed_urls",
    )
