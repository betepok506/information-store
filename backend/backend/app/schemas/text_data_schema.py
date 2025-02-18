from backend.app.models.text_data_model import TextDataBase
from backend.app.models.processed_urls_model import ProcessedUrlsBase
from backend.app.utils.partial import optional
from uuid import UUID

# from .user_schema import IUserReadWithoutGroups


class ITextDataRequest(TextDataBase):
    url: str  # URL адресс откуда взят текст
    source_name: str  # Имя источника


class ITextDataCreate(TextDataBase):
    processed_urls_by_id: UUID


# class IListTextDataCreate(TextDataBase):
#     items: ITextDataCreate
# processed_urls_by_id: UUID


class IProcessedUrlsReadBasic(ProcessedUrlsBase):
    id: UUID


class ITextDataRead(TextDataBase):
    id: UUID
    processed_urls_by: IProcessedUrlsReadBasic | None = None


@optional()
class ITextDataUpdateRequest(ITextDataRequest):
    url: str
    source_name: str


# All these fields are optional
@optional()
class ITextDataUpdate(ITextDataCreate):
    pass
