from uuid import UUID
from typing import List
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
from backend.app.utils.exceptions import (
    IdNotFoundException,
    SourceNotFoundException,
)
from fastapi_pagination import Page, Params
from backend.app.schemas.source_schema import ISourceCreate
from backend.app import crud
from backend.app.utils.hash import get_hash
from backend.app.utils.map_schema import merge_schemas


class TextDataManager:
    """Класс, реализует сервисную логику взаимодействия с таблицей TextData"""

    def __init__(self, db: AsyncSession, es: AsyncElasticsearch | None = None):
        self.db = db
        self.es = es

    async def get_text_data(self, params) -> Page[ITextDataReadBasic]:
        query = (
            select(TextData, ProcessedUrls, Source)
            .join(
                ProcessedUrls,
                TextData.processed_urls_id == ProcessedUrls.id,
                isouter=True,
            )
            .join(Source, ProcessedUrls.source_id == Source.id, isouter=True)
        )
        groups = await crud.text_data.get_multi_paginated(
            db_session=self.db, params=params, query=query
        )
        return groups

    async def get_text_data_by_id(
        self, text_data_id: UUID
    ) -> ITextDataReadBasic | None:
        return await crud.text_data.get(db_session=self.db, id=text_data_id)

    async def get_by_elastic_ids_paginated(
        self, elastic_ids: List[str], params: Params
    ) -> Page[ITextDataReadBasic]:
        query = (
            select(TextData, ProcessedUrls, Source)
            .join(
                ProcessedUrls,
                TextData.processed_urls_id == ProcessedUrls.id,
                isouter=True,
            )
            .join(Source, ProcessedUrls.source_id == Source.id, isouter=True)
            .where(TextData.elastic_id.in_(elastic_ids))  # Фильтрация по массиву ID
        )
        result = await crud.text_data.get_by_elastic_ids_paginated(
            db_session=self.db, query=query, params=params
        )
        return result

    async def create_text_data(
        self, obj_in: ITextDataCreateRequest, index: str
    ) -> ITextDataReadFull:
        """Функция реализует функционал создания объекта в базе данных"""

        async def _create_operation():
            source = await self._get_or_create_source(
                obj_in.source_name, obj_in.url, self.db
            )

            hashed_str = get_hash(obj_in.text)
            processed_url = IProcessedUrlsCreate(
                url=obj_in.url, source_id=source.id, hash=hashed_str
            )

            # Добавление обработанного url в базу данных
            new_processed_url = await crud.processed_urls.create(
                db_session=self.db, obj_in=processed_url
            )
            print(7)
            # Elasticsearch
            elastic_id = await self._create_elastic_record(
                index, obj_in.text, obj_in.vector
            )

            text_data = ITextDataCreate(
                text=obj_in.text,
                elastic_id=elastic_id,
                processed_urls_id=new_processed_url.id,
            )
            new_text_data = await crud.text_data.create(
                db_session=self.db, obj_in=text_data
            )

            return ITextDataReadFull(
                id=new_text_data.id,
                url=obj_in.url,
                # processed_urls=new_text_data.processed_urls,
                processed_urls_id=new_processed_url.id,
                text=new_text_data.text,
                elastic_id=new_text_data.elastic_id,
                vector=obj_in.vector,
            )

        return await self._execute_in_transaction(_create_operation)

    async def update_text_data(
        self, obj_in: ITextDataUpdateRequest, index: str, text_data_id: str
    ) -> ITextDataReadFull:
        async def _update_operation():
            cur_text_data = await crud.text_data.get_db_object(
                db_session=self.db, id=text_data_id
            )
            if not cur_text_data:
                raise IdNotFoundException(TextData, cur_text_data)

            current_processed_url = await crud.processed_urls.get(
                db_session=self.db, id=cur_text_data.processed_urls_id
            )
            if not current_processed_url:
                raise IdNotFoundException(
                    ProcessedUrls, id=cur_text_data.processed_urls_id
                )

            source = await crud.source.get(
                db_session=self.db, id=current_processed_url.source_id
            )
            if not source:
                raise IdNotFoundException(Source, id=text_data_id)

            hashed_str = None
            if not obj_in.text is None:
                hashed_str = get_hash(obj_in.text)

            processed_urls_params = {
                "url": obj_in.url,
                "hash": hashed_str,
                "source_id": source.id,
            }
            updated_processed_url = IProcessedUrlsUpdate(
                **{
                    key: value
                    for key, value in processed_urls_params.items()
                    if value is not None
                }
            )

            updated_processed_url = await crud.processed_urls.update(
                db_session=self.db,
                obj_current=current_processed_url,
                obj_new=updated_processed_url,
            )

            # Обновление вектора в Elastic Search
            elastic_id = None
            if obj_in.vector is not None:
                item = await self.es.update(
                    index=index,
                    id=cur_text_data.elastic_id,
                    body={
                        "doc": {  # Обязательный блок для update
                            "text": obj_in.text,
                            "vector": obj_in.vector,
                        }
                    },
                )
                elastic_id = item["_id"]

            response = await self.es.get(index=index, id=cur_text_data.elastic_id)
            vector = response.body["_source"]["vector"]

            updated_text_data = ITextDataUpdate()
            values = {
                "elastic_id": elastic_id,
                "processed_urls_id": updated_processed_url.id,
            }
            updated_text_data = merge_schemas(updated_text_data, obj_in, values)
            obj_updated_text_data = await crud.text_data.update(
                db_session=self.db, obj_current=cur_text_data, obj_new=updated_text_data
            )

            return ITextDataReadFull(
                id=obj_updated_text_data.id,
                text=obj_updated_text_data.text,
                elastic_id=obj_updated_text_data.elastic_id,
                url=updated_processed_url.url,
                processed_urls_id=updated_processed_url.id,
                vector=vector,
            )

        return await self._execute_in_transaction(_update_operation)

    async def _create_elastic_record(
        self, index: str, text: str, vector: List[float]
    ) -> str:
        """Создание записи в Elasticsearch с обработкой ошибок"""
        try:
            response = await self.es.index(
                index=index, body={"text": text, "vector": vector}
            )
            return response["_id"]
        except Exception as e:
            raise RuntimeError(f"Elasticsearch error: {str(e)}") from e

    async def _get_or_create_source(
        self, name: str, url: str, db_session: AsyncSession | None = None
    ) -> Source:
        source = await crud.source.get_by_name(db_session=self.db, name=name)
        if not source:
            # Если нет источника, создаем его
            source = await crud.source.create(
                db_session=db_session,
                obj_in=ISourceCreate(name=name, url=url)
            )
            print(f'Created source')
        return source

    async def _execute_in_transaction(self, operation, *args, **kwargs):
        # """Выполняет операцию в контексте существующей транзакции"""
        # async with self.db.begin():
        #     try:
        #         return await operation(*args, **kwargs)
        #     except Exception as e:
        #         await self.db.rollback()
        #         raise

        """Выполняет операцию в контексте существующей транзакции"""
        if self.db.in_transaction():
            return await operation(*args, **kwargs)

        async with self.db.begin():
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                await self.db.rollback()
                raise
