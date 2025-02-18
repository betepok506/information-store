# from backend.app.models.user_model import User
from sqlmodel import Field, SQLModel

from backend.app.models.base_uuid_model import BaseUUIDModel

# from uuid import UUID


class SourceBase(SQLModel):
    name: str = Field(index=True)
    url: str


class Source(BaseUUIDModel, SourceBase, table=True):
    pass
