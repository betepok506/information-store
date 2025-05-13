from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from app.models.base_uuid_model import BaseUUIDModel

if TYPE_CHECKING:
    from app.models import ProcessedUrls

__all__ = ["TextDataBase", "TextData"]


class TextDataBase(SQLModel):
    text: str = Field(index=True)
    elastic_id: str


class TextData(BaseUUIDModel, TextDataBase, table=True):
    processed_urls_id: UUID | None = Field(
        default=None, foreign_key="ProcessedUrls.id", ondelete="SET NULL"
    )
    processed_urls: Optional["ProcessedUrls"] | None = (
        Relationship(  # noqa: F821
            sa_relationship_kwargs={
                "lazy": "joined",
                "primaryjoin": "TextData.processed_urls_id==ProcessedUrls.id",
                "cascade": "delete",
            },
            back_populates="text_data",
        )
    )
