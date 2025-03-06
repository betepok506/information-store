from uuid import UUID

from backend.app.models.processed_urls_model import ProcessedUrlsBase
from backend.app.models.text_data_model import TextDataBase
from backend.app.utils.partial import optional


class ITextDataRequest(TextDataBase):
    url: str  # URL адресс откуда взят текст
    source_name: str  # Имя источника


class ITextDataCreate(TextDataBase):
    processed_urls_id: UUID


class IProcessedUrlsReadBasic(ProcessedUrlsBase):
    id: UUID


class ITextDataRead(TextDataBase):
    id: UUID
    processed_urls: IProcessedUrlsReadBasic | None = None


@optional()
class ITextDataUpdateRequest(ITextDataRequest):
    pass


# All these fields are optional
@optional()
class ITextDataUpdate(ITextDataCreate):
    pass
