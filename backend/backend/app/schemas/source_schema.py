# from backend.app.models.hero_model import HeroBase
from uuid import UUID

from backend.app.models.source_model import SourceBase

# from .user_schema import IUserBasicInfo
from backend.app.utils.partial import optional


class ISourceCreate(SourceBase):
    pass


# All these fields are optional
@optional()
class ISourceUpdate(SourceBase):
    pass


class ISourceRead(SourceBase):
    id: UUID
    # created_by: IUserBasicInfo


# class ITeamReadWithHeroes(ITeamRead):
#     heroes: list[HeroBase]
