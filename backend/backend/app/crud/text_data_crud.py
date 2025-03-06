from sqlmodel import select
from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlmodel import paginate
from backend.app.crud.base_crud import CRUDBase, ModelType, T
from backend.app.models.text_data_model import TextData
from backend.app.models.source_model import Source
from backend.app.models.processed_urls_model import ProcessedUrls
from backend.app.schemas.text_data_schema import ITextDataCreate, ITextDataUpdate
from backend.app.schemas.text_data_schema import (
    ITextDataCreateRequest,
    ITextDataUpdateRequest,
    ITextDataReadBasic,
)
from typing import Any
from sqlmodel.sql.expression import Select


class CRUDTextData(CRUDBase[TextData, ITextDataCreate, ITextDataUpdate]):
    async def get(
        self, *, id: UUID | str, db_session: AsyncSession | None = None
    ) -> ITextDataReadBasic | None:
        """Возвращает объект необходимый для пользователя"""
        db_session = db_session or self.db.session
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
        structured_results = await self._conversion_to_schemas_read_basic([result])
        return structured_results[0]  # Проверить если объект не найден

    async def get_db_object(
        self, *, id: UUID | str, db_session: AsyncSession | None = None
    ) -> ModelType | None:
        """Метод возвращает объект базы данных"""
        db_session = db_session or self.db.session
        query = select(self.model).where(self.model.id == id)
        response = await db_session.execute(query)
        return response.scalar_one_or_none()

    # async def get_by_elastic_ids(
    #     self,
    #     *,
    #     list_ids: list[UUID | str],
    #     skip: int = 0,
    #     limit: int = 100,
    #     db_session: AsyncSession | None = None,
    # ) -> list[ModelType] | None:
    #     db_session = db_session or self.db.session
    #     response = await db_session.execute(
    #         select(self.model)
    #         .offset(skip)
    #         .limit(limit)
    #         .where(self.model.elastic_id.in_(list_ids))
    #     )
    #     return response.scalars().all()

    async def get_multi_paginated(
        self,
        *,
        params: Params | None = Params(),
        query: T | Select[T] | None = None,
        db_session: AsyncSession | None = None,
    ) -> Page[ITextDataReadBasic]:
        db_session = db_session or self.db.session
        if query is None:
            query = select(self.model)

        output = await paginate(db_session, query, params)
        structured_results = await self._conversion_to_schemas_read_basic(output.items)
        return Page(
            items=structured_results,
            total=output.total,
            page=output.page,
            size=output.size,
        )

    async def get_by_elastic_ids_paginated(
        self,
        *,
        params: Params | None = Params(),
        query: T | Select[T] | None = None,
        db_session: AsyncSession | None = None,
    ) -> Page[ITextDataReadBasic]:
        db_session = db_session or self.db.session
        if query is None:
            query = select(self.model)

        output = await paginate(db_session, query, params)
        # Преобразование результата в нужный формат
        structured_results = await self._conversion_to_schemas_read_basic(output.items)
        return Page(
            items=structured_results,
            total=output.total,
            page=output.page,
            size=output.size,
        )

    async def get_group_by_name(
        self, *, name: str, db_session: AsyncSession | None = None
    ) -> TextData:
        db_session = db_session or super().get_db().session
        group = await db_session.execute(select(TextData).where(TextData.name == name))
        return group.scalar_one_or_none()

    async def _conversion_to_schemas_read_basic(self, items):
        structured_results = []
        for text_data, processed_urls, source in items:
            structured_results.append(
                ITextDataReadBasic(
                    id=text_data.id,
                    text=text_data.text,
                    elastic_id=text_data.elastic_id,
                    url=source.url + processed_urls.suf_url,
                    processed_urls_id=processed_urls.id,
                )
            )
        return structured_results

    async def remove(
        self, *, id: UUID | str, db_session: AsyncSession | None = None
    ) -> ITextDataReadBasic:
        db_session = db_session or self.db.session
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
        structured_results = await self._conversion_to_schemas_read_basic([result])
        obj, _, _ = result
        await db_session.delete(obj)
        await db_session.commit()
        return structured_results[0]

text_data = CRUDTextData(TextData)
