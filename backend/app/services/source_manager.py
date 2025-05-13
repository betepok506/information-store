"""
Модуль для управления источниками данных.

Содержит логику работы с источниками (Source):

    - создание;
    - чтение;
    - обновление;
    - удаление.
"""

from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi_pagination import Page
from sqlmodel.ext.asyncio.session import AsyncSession

from app import crud
from app.models import Source
from app.schemas import ISourceCreate, ISourceRead, ISourceUpdate
from app.utils.exceptions import (
    ContentNoChangeException,
    IdNotFoundException,
    SourceExistException,
    SourceNotFoundException,
)

__all__ = ["SourceManager"]


class SourceManager:
    """
    Менеджер для работы с источниками данных.

    Обеспечивает CRUD-операции и бизнес-логику для сущности Source.

    Attributes
    ----------
    db : AsyncSession
        Асинхронная сессия SQLAlchemy
    es : AsyncElasticsearch | None
        Клиент Elasticsearch (необязательный)
    """

    def __init__(self, db: AsyncSession, es: AsyncElasticsearch | None = None):
        """
        Инициализация менеджера источников.

        Parameters:
            db : AsyncSession
                Асинхронная сессия SQLAlchemy
            es : AsyncElasticsearch | None
                Опциональный клиент Elasticsearch
        """
        self.db = db
        self.es = es

    async def get_sources_list(self, params) -> Page[ISourceRead]:
        """Получить пагинированный список источников.

        :param params: Параметры пагинации и фильтрации
        :return: Страница с результатами в формате ISourceRead
        :rtype: Page[ISourceRead]
        """
        sources = await crud.source.get_multi_paginated(
            db_session=self.db, params=params
        )
        return sources

    async def get_source_id(self, source_id: UUID) -> ISourceRead | None:
        """
        Получает источник по его идентификатору.

        Parameters
        ----------
        source_id : UUID
            UUID идентификатор источника

        Returns
        -------
        ISourceRead | None
            Объект источника или None если не найден

        Raises
        ------
        IdNotFoundException
            Если источник с указанным ID не найден
        """
        source = await crud.source.get(db_session=self.db, id=source_id)
        if not source:
            raise IdNotFoundException(Source, id=source_id)
        return source

    async def create_source(self, obj_in: ISourceCreate) -> ISourceRead:
        """
        Создает новый источник данных.

        Parameters
        ----------
        obj_in : ISourceCreate
            Входные данные для создания

        Returns
        -------
        ISourceRead
            Созданный объект источника

        Raises
        ------
        SourceExistException
            Если источник с таким именем уже существует
        """

        async def _create_operation():
            source_current = await crud.source.get_by_name(
                db_session=self.db, name=obj_in.name
            )
            if source_current:
                raise SourceExistException(Source, name=source_current.name)

            source = await crud.source.create(
                db_session=self.db, obj_in=obj_in
            )
            return source

        return await self._execute_in_transaction(_create_operation)

    async def update_source(
        self, source_id: UUID, new_source: ISourceUpdate
    ) -> ISourceRead:
        """Обновить существующий источник данных.

        :param source_id: UUID идентификатор обновляемого источника
        :type source_id: UUID
        :param new_source: Новые данные для обновления
        :type new_source: ISourceUpdate
        :return: Обновленный объект источника
        :rtype: ISourceRead
        :raises IdNotFoundException: Если источник не найден
        :raises ContentNoChangeException: Если данные не изменились
        :raises SourceExistException: Если новое имя уже занято
        """

        async def _update_operation():
            current_source = await crud.source.get(
                db_session=self.db, id=source_id
            )
            if not current_source:
                raise IdNotFoundException(Source, id=source_id)

            if (
                current_source.name == new_source.name
                and current_source.url == new_source.url
            ):
                raise ContentNoChangeException(
                    detail="The content has not changed"
                )

            # TODO: Проверить условия обновления элемента
            exist_source = await crud.source.get_by_name(
                db_session=self.db, name=new_source.name
            )
            if exist_source:
                raise SourceExistException(Source, name=exist_source.name)

            source_updated = await crud.source.update(
                db_session=self.db,
                obj_current=current_source,
                obj_new=new_source,
            )
            return source_updated

        return await self._execute_in_transaction(_update_operation)

    async def remove_source(self, source_id: UUID) -> ISourceRead:
        """Удалить источник данных.

        :param source_id: UUID идентификатор удаляемого источника
        :type source_id: UUID
        :return: Удаленный объект источника
        :rtype: ISourceRead
        :raises IdNotFoundException: Если источник не найден
        """

        async def _remove_operation():
            current_source = await crud.source.get(
                db_session=self.db, id=source_id
            )
            if not current_source:
                raise IdNotFoundException(Source, id=source_id)

            source = await crud.source.remove(db_session=self.db, id=source_id)
            return source

        return await self._execute_in_transaction(_remove_operation)

    async def check_source_by_name(self, name: str) -> ISourceRead:
        """
        Проверка существования источника по имени.

        Parameters:
            name : str
                Имя источника для поиска

        Returns:
            ISourceRead: Найденный объект источника

        Raises:
            SourceNotFoundException: Если источник не найден
        """
        source = await crud.source.get_by_name(db_session=self.db, name=name)
        if not source:
            raise SourceNotFoundException(Source, source=name)

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
