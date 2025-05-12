"""
Модуль для управления текстовыми данными и векторами.

Интегрирует операции с:
- Реляционной БД (PostgreSQL)
- Поисковым движком (Elasticsearch)
- Очередями сообщений
"""

from typing import List
from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi_pagination import Page, Params
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app import crud
from app.models import ProcessedUrls, Source, TextData
from app.schemas import (
    IProcessedUrlsCreate,
    IProcessedUrlsUpdate,
    ISourceCreate,
    ITextDataCreate,
    ITextDataCreateRequest,
    ITextDataReadBasic,
    ITextDataReadFull,
    ITextDataUpdate,
    ITextDataUpdateRequest,
)
from app.utils.exceptions import IdNotFoundException
from app.utils.hash import get_hash
from app.utils.map_schema import merge_schemas

__all__ = ["TextDataManager"]


class TextDataManager:
    """
    Универсальный менеджер для работы с текстовыми данными.

    Объединяет:
    - Хранение метаданных в PostgreSQL
    - Векторный поиск через Elasticsearch
    - Транзакционное выполнение операций

    Attributes
    ----------
    db : AsyncSession
        Асинхронная сессия SQLAlchemy
    es : AsyncElasticsearch | None
        Клиент Elasticsearch (необязательный)
    """

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
            .where(
                TextData.elastic_id.in_(elastic_ids)
            )  # Фильтрация по массиву ID
        )
        result = await crud.text_data.get_by_elastic_ids_paginated(
            db_session=self.db, query=query, params=params
        )
        return result

    async def create_text_data(
        self, obj_in: ITextDataCreateRequest, index: str
    ) -> ITextDataReadFull:
        """
        Создает новую запись текстовых данных.

        Parameters
        ----------
        obj_in : ITextDataCreateRequest
            Входные данные для создания
        index : str
            Название индекса в Elasticsearch

        Returns
        -------
        ITextDataReadFull
            Полная информация о созданной записи

        Raises
        ------
        RuntimeError
            При ошибке взаимодействия с Elasticsearch
        """

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
        """
        Обновляет существующую запись текстовых данных.

        Parameters
        ----------
        obj_in : ITextDataUpdateRequest
            Новые данные для обновления
        index : str
            Название индекса в Elasticsearch
        text_data_id : str
            Идентификатор обновляемой записи

        Returns
        -------
        ITextDataReadFull
            Обновленная информация о записи

        Raises
        ------
        IdNotFoundException
            Если запись не найдена
        RuntimeError
            При ошибке обновления в Elasticsearch
        """

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
            if obj_in.text is not None:
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

            response = await self.es.get(
                index=index, id=cur_text_data.elastic_id
            )
            vector = response.body["_source"]["vector"]

            updated_text_data = ITextDataUpdate()
            values = {
                "elastic_id": elastic_id,
                "processed_urls_id": updated_processed_url.id,
            }
            updated_text_data = merge_schemas(
                updated_text_data, obj_in, values
            )
            obj_updated_text_data = await crud.text_data.update(
                db_session=self.db,
                obj_current=cur_text_data,
                obj_new=updated_text_data,
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
        """
        Создание записи в Elasticsearch.

        Parameters:
            index : str
                Название индекса для сохранения
            text : str
                Текст для индексации
            vector : List[float]
                Векторное представление текста

        Returns:
            str: Идентификатор созданной записи

        Raises:
            RuntimeError: При ошибках Elasticsearch
        """
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
        """
        Получение или создание источника данных.

        Parameters:
            name : str
                Название источника
            url : str
                URL источника
            db_session : AsyncSession | None
                Опциональная сессия БД

        Returns:
            Source: Объект источника

        Notes:
            Если источник не существует - создает новый
        """
        source = await crud.source.get_by_name(db_session=self.db, name=name)
        if not source:
            # Если нет источника, создаем его
            source = await crud.source.create(
                db_session=db_session, obj_in=ISourceCreate(name=name, url=url)
            )
            print("Created source")
        return source

    async def _execute_in_transaction(self, operation, *args, **kwargs):
        """
        Приватный метод для выполнения операций в транзакции.

        Parameters:
            operation : Callable
                Асинхронная функция-операция
            *args:
                Аргументы операции
            **kwargs:
                Именованные аргументы операции

        Returns:
            Any: Результат выполнения операции

        Raises:
            Exception: При ошибке с откатом транзакции
        """
        if self.db.in_transaction():
            return await operation(*args, **kwargs)

        async with self.db.begin():
            try:
                return await operation(*args, **kwargs)
            except Exception:
                await self.db.rollback()
                raise
