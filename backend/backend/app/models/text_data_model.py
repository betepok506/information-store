from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from backend.app.models.base_uuid_model import BaseUUIDModel
from backend.app.models.processed_urls_model import ProcessedUrls


class TextDataBase(SQLModel):
    text: str = Field(index=True)
    elastic_id: str


class TextData(BaseUUIDModel, TextDataBase, table=True):
    processed_urls_by_id: UUID | None = Field(
        default=None, foreign_key="ProcessedUrls.id"
    )
    processed_urls_by: ProcessedUrls | None = Relationship(  # noqa: F821
        sa_relationship_kwargs={
            "lazy": "joined",
            "primaryjoin": "TextData.processed_urls_by_id==ProcessedUrls.id",
        }
    )
