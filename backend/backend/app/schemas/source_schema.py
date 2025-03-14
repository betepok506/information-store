from uuid import UUID
from backend.app.models.source_model import SourceBase
from backend.app.utils.partial import optional


class ISourceCreate(SourceBase):
    pass


# All these fields are optional
@optional()
class ISourceUpdate(SourceBase):
    pass


class ISourceRead(SourceBase):
    id: UUID
