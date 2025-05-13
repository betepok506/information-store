from uuid import UUID

from app.models import SourceBase
from app.utils.partial import optional

__all__ = ["ISourceCreate", "ISourceUpdate", "ISourceRead"]


class ISourceCreate(SourceBase):
    pass


# All these fields are optional
@optional()
class ISourceUpdate(SourceBase):
    pass


class ISourceRead(SourceBase):
    id: UUID
