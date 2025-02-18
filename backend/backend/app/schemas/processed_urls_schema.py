# from backend.app.models.hero_model import HeroBase
from uuid import UUID

from backend.app.models.processed_urls_model import ProcessedUrlsBase

# from .user_schema import IUserBasicInfo
from backend.app.utils.partial import optional


class IProcessedUrlsCreate(ProcessedUrlsBase):
    source_by_id: UUID


# All these fields are optional
@optional()
class IProcessedUrlsUpdate(ProcessedUrlsBase):
    class Config:
        exclude_unset = True


class IProcessedUrlsRead(ProcessedUrlsBase):
    id: UUID
    # created_by: IUserBasicInfo


# class ITeamReadWithHeroes(ITeamRead):
#     heroes: list[HeroBase]
