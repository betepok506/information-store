from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from backend.app.models.base_uuid_model import BaseUUIDModel
from backend.app.models.source_model import Source


class ProcessedUrlsBase(SQLModel):
    suf_url: str = Field(index=True)
    hash: str = Field(index=True)


class ProcessedUrls(BaseUUIDModel, ProcessedUrlsBase, table=True):
    source_by_id: UUID | None = Field(default=None, foreign_key="Source.id")
    source_by: Source | None = Relationship(  # noqa: F821
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "ProcessedUrls.source_by_id==Source.id",
        }
    )
