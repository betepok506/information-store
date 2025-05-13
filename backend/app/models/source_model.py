from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import relationship as sa_relationship
from sqlmodel import Field, Relationship, SQLModel

from .base_uuid_model import BaseUUIDModel

if TYPE_CHECKING:
    from app.models import ProcessedUrls
    
__all__ = ["SourceBase", "Source"]


class SourceBase(SQLModel):
    name: str = Field(index=True)
    url: str


class Source(BaseUUIDModel, SourceBase, table=True):
    processed_urls: Optional["ProcessedUrls"] = Relationship(
        sa_relationship=sa_relationship(
            "ProcessedUrls", cascade="all, delete-orphan", lazy="selectin"
        ),
        back_populates="source",
    )
