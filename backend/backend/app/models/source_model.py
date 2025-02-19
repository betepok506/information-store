# from backend.app.models.user_model import User
from sqlmodel import Field, SQLModel
from sqlalchemy.orm import relationship as sa_relationship
from backend.app.models.base_uuid_model import BaseUUIDModel
# from backend.app.models.processed_urls_model import ProcessedUrls
from sqlmodel import Relationship
# from uuid import UUID
from typing import List, Optional

class SourceBase(SQLModel):
    name: str = Field(index=True)
    url: str


class Source(BaseUUIDModel, SourceBase, table=True):
    # pass
    processed_urls: Optional["ProcessedUrls"] = Relationship(
        sa_relationship=sa_relationship("ProcessedUrls", cascade="all, delete-orphan", lazy="selectin"),
        back_populates="source",
    )
