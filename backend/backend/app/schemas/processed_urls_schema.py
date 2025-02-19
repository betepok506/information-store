# from backend.app.models.hero_model import HeroBase
from uuid import UUID
from pydantic import BaseModel
from backend.app.models.processed_urls_model import ProcessedUrlsBase
from backend.app.models.text_data_model import TextDataBase
from backend.app.models.source_model import SourceBase

# from .user_schema import IUserBasicInfo
from backend.app.utils.partial import optional


class IProcessedUrlsCreate(ProcessedUrlsBase):
    source_id: UUID


# All these fields are optional
@optional()
class IProcessedUrlsUpdate(ProcessedUrlsBase):
    class Config:
        exclude_unset = True

class ISourceReadBasic(SourceBase):
    id: UUID
    

class IProcessedUrlsResponse(BaseModel):
    id: UUID | int
    url: str
    source_name: str
    


class IProcessedUrlsRead(ProcessedUrlsBase):
    id: UUID
    source: ISourceReadBasic | None = None


# class ITeamReadWithHeroes(ITeamRead):
#     heroes: list[HeroBase]
