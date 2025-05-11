from uuid import UUID

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlmodel import paginate
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select

from app.models import ProcessedUrls, Source, TextData
from app.schemas import (
    ITextDataCreate,
    ITextDataReadBasic,
    ITextDataUpdate,
)

from .base_crud import CRUDBase, ModelType, T

__all__ = ["text_data"]


class CRUDTextData(CRUDBase[TextData, ITextDataCreate, ITextDataUpdate]):
    async def get(
        self, *, db_session: AsyncSession, id: UUID | str
    ) -> ITextDataReadBasic | None:
        """Возвращает объект необходимый для пользователя"""
        query = (
            select(TextData, ProcessedUrls, Source)
            .join(
                ProcessedUrls,
                TextData.processed_urls_id == ProcessedUrls.id,
                isouter=True,
            )
            .join(Source, ProcessedUrls.source_id == Source.id, isouter=True)
            .where(TextData.id == id)
        )

        response = await db_session.execute(query)
        result = response.first()
        structured_results = await self._conversion_to_schemas_read_basic(
            [result]
        )
        return structured_results[0]  # Проверить если объект не найден

    async def get_db_object(
        self, *, db_session: AsyncSession, id: UUID | str
    ) -> ModelType | None:
        """Метод возвращает объект базы данных"""
        query = select(self.model).where(self.model.id == id)
        response = await db_session.execute(query)
        return response.scalar_one_or_none()

    async def get_multi_paginated(
        self,
        *,
        db_session: AsyncSession,
        params: Params | None = Params(),
        query: T | Select[T] | None = None,
    ) -> Page[ITextDataReadBasic]:
        if query is None:
            query = select(self.model)

        output = await paginate(db_session, query, params)
        structured_results = await self._conversion_to_schemas_read_basic(
            output.items
        )
        return Page(
            items=structured_results,
            total=output.total,
            page=output.page,
            size=output.size,
        )

    async def get_by_elastic_ids_paginated(
        self,
        *,
        db_session: AsyncSession,
        params: Params | None = Params(),
        query: T | Select[T] | None = None,
    ) -> Page[ITextDataReadBasic]:
        if query is None:
            query = select(self.model)

        output = await paginate(db_session, query, params)
        # Преобразование результата в нужный формат
        structured_results = await self._conversion_to_schemas_read_basic(
            output.items
        )
        return Page(
            items=structured_results,
            total=output.total,
            page=output.page,
            size=output.size,
        )

    async def get_group_by_name(
        self, *, db_session: AsyncSession, name: str
    ) -> TextData:
        group = await db_session.execute(
            select(TextData).where(TextData.name == name)
        )
        return group.scalar_one_or_none()

    async def _conversion_to_schemas_read_basic(self, items):
        structured_results = []
        for text_data, processed_urls, source in items:
            structured_results.append(
                ITextDataReadBasic(
                    id=text_data.id,
                    text=text_data.text,
                    elastic_id=text_data.elastic_id,
                    url=processed_urls.url,
                    # processed_urls_id=processed_urls.id,
                )
            )
        return structured_results

    async def remove(
        self, *, db_session: AsyncSession, id: UUID | str
    ) -> ITextDataReadBasic:
        query = (
            select(TextData, ProcessedUrls, Source)
            .join(
                ProcessedUrls,
                TextData.processed_urls_id == ProcessedUrls.id,
                isouter=True,
            )
            .join(Source, ProcessedUrls.source_id == Source.id, isouter=True)
            .where(TextData.id == id)
        )

        response = await db_session.execute(query)
        result = response.first()
        structured_results = await self._conversion_to_schemas_read_basic(
            [result]
        )
        obj, _, _ = result
        await db_session.delete(obj)
        await db_session.flush()
        return structured_results[0]


text_data = CRUDTextData(TextData)
