from uuid import UUID
from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from backend.app.models import TextData, ProcessedUrls, Source
from elasticsearch import AsyncElasticsearch
from backend.app.schemas.text_data_schema import (
    ITextDataCreate,
    ITextDataUpdate,
    ITextDataUpdateRequest,
    ITextDataCreateRequest,
    ITextDataReadBasic,
    ITextDataReadFull,
)
from backend.app.schemas.processed_urls_schema import (
    IProcessedUrlsCreate,
    IProcessedUrlsUpdate,
)
from backend.app.schemas.source_schema import ISourceCreate
from backend.app import crud
from backend.app.utils.hash import get_hash

class TextDataService:
    '''Класс, реализует сервисную логику взаимодействия с таблицей TextData'''
    def __init__(self):
        pass
        # self.db = db

    async def create_text_data(self, obj_in: ITextDataCreateRequest, es: AsyncElasticsearch, db_session: AsyncSession | None = None) -> ITextDataReadFull:
        '''Функция реализует функционал создания объекта в базе данных'''
        source = await self._get_or_create_source(obj_in.source_name, obj_in.url, db_session)
        hashed_str = get_hash(obj_in.text)
        
        processed_url = IProcessedUrlsCreate(
            url=obj_in.url,
            source_id=source.id,
            hash=hashed_str
        )
        # Добавление обработанного url в базу данных
        new_processed_url = await crud.processed_urls.create(obj_in=processed_url, db_session=db_session)
        
        # Elasticsearch integration
        try:
            item = await es.index(
                index="text_vectors",
                body={"text": obj_in.text, "vector": obj_in.vector}
            )
            elastic_id = item["_id"]
        except Exception as e:
            raise
        
        text_data = ITextDataCreate(
            text=obj_in.text,
            elastic_id=elastic_id,
            processed_urls_id=new_processed_url.id
        )
        new_text_data = await crud.text_data.create(obj_in=text_data,db_session=db_session)
        
        return ITextDataReadFull(
            id=new_text_data.id,
            url=obj_in.url,
            # processed_urls=new_text_data.processed_urls,
            processed_urls_id=new_processed_url.id,
            text=new_text_data.text,
            elastic_id=new_text_data.elastic_id,
            vector=obj_in.vector,
        )

    async def _get_or_create_source(self, name: str, url: str, db_session: AsyncSession | None = None) -> Source:
        source = await crud.source.get_source_by_name(name=name, db_session=db_session)
        if not source:
            # Если нет источника, создаем его
            source = await crud.source.create(obj_in=ISourceCreate(name=name, url=url,db_session=db_session))
        return source

    # async def get_by_elastic_ids(self, elastic_ids: List[str]) -> List[TextData]:
    #     result = await self.db.execute(
    #         select(TextData).where(TextData.elastic_id.in_(elastic_ids))
    #     )
    #     return result.scalars().all()

    # async def update_text_data(self, text_data_id: UUID, obj_in: ITextDataUpdateRequest) -> ITextDataReadFull:
    #     # Полная реализация логики обновления
    #     # (аналогично вашей текущей реализации, но перенесенная в сервис)
    #     pass