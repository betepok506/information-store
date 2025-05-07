from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.models import Source
from elasticsearch import AsyncElasticsearch
from backend.app.utils.exceptions import (
    IdNotFoundException,
    SourceNotFoundException,
)
from fastapi_pagination import Page
from backend.app.schemas.source_schema import ISourceCreate
from backend.app import crud
from backend.app.schemas.source_schema import ISourceCreate, ISourceRead, ISourceUpdate
from backend.app.utils.exceptions import (
    ContentNoChangeException,
    IdNotFoundException,
    SourceExistException,
    SourceNotFoundException,
)


class SourceManager:
    """Класс, реализует сервисную логику взаимодействия с таблицей Source"""

    def __init__(self, db: AsyncSession, es: AsyncElasticsearch | None = None):
        self.db = db
        self.es = es

    async def get_sources_list(self, params) -> Page[ISourceRead]:
        sources = await crud.source.get_multi_paginated(
            db_session=self.db, params=params
        )
        return sources

    async def get_source_id(self, source_id: UUID) -> ISourceRead | None:
        source = await crud.source.get(db_session=self.db, id=source_id)
        if not source:
            raise IdNotFoundException(Source, id=source_id)
        return source

    async def create_source(self, obj_in: ISourceCreate) -> ISourceRead:
        """Функция реализует функционал создания объекта в базе данных"""

        async def _create_operation():
            source_current = await crud.source.get_by_name(
                db_session=self.db, name=obj_in.name
            )
            if source_current:
                raise SourceExistException(Source, name=source_current.name)

            source = await crud.source.create(db_session=self.db, obj_in=obj_in)
            return source

        return await self._execute_in_transaction(_create_operation)

    async def update_source(
        self, source_id: UUID, new_source: ISourceUpdate
    ) -> ISourceRead:
        """Функция реализует функционал обновления объекта в базе данных"""

        async def _update_operation():
            current_source = await crud.source.get(db_session=self.db, id=source_id)
            if not current_source:
                raise IdNotFoundException(Source, id=source_id)

            if (
                current_source.name == new_source.name
                and current_source.url == new_source.url
            ):
                raise ContentNoChangeException(detail="The content has not changed")

            # TODO: Проверить условия обновления элемента
            exist_source = await crud.source.get_by_name(
                db_session=self.db,
                name=new_source.name
            )
            if exist_source:
                raise SourceExistException(Source, name=exist_source.name)

            source_updated = await crud.source.update(
                db_session=self.db, obj_current=current_source, obj_new=new_source
            )
            return source_updated

        return await self._execute_in_transaction(_update_operation)

    async def remove_source(self, source_id: UUID) -> ISourceRead:
        """Функция реализует функционал удаления объекта с базы данных"""

        async def _remove_operation():
            current_source = await crud.source.get(db_session=self.db, id=source_id)
            if not current_source:
                raise IdNotFoundException(Source, id=source_id)

            source = await crud.source.remove(db_session=self.db, id=source_id)
            return source

        return await self._execute_in_transaction(_remove_operation)

    async def check_source_by_name(self, name: str) -> ISourceRead:
        source = await crud.source.get_by_name(db_session=self.db, name=name)
        if not source:
            raise SourceNotFoundException(Source, source=name)

        return source

    async def _execute_in_transaction(self, operation, *args, **kwargs):
        """Выполняет операцию в контексте существующей транзакции"""
        if self.db.in_transaction():
            return await operation(*args, **kwargs)

        async with self.db.begin():
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                await self.db.rollback()
                raise
