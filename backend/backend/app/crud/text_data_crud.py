from sqlmodel import select
from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlmodel import paginate
from backend.app.crud.base_crud import CRUDBase, ModelType, T
from backend.app.models.text_data_model import TextData
from backend.app.schemas.text_data_schema import ITextDataCreate, ITextDataUpdate
from sqlmodel.sql.expression import Select


class CRUDTextData(CRUDBase[TextData, ITextDataCreate, ITextDataUpdate]):
    async def get_by_elastic_ids(
        self,
        *,
        list_ids: list[UUID | str],
        skip: int = 0,
        limit: int = 100,
        db_session: AsyncSession | None = None,
    ) -> list[ModelType] | None:
        db_session = db_session or self.db.session
        response = await db_session.execute(
            select(self.model)
            .offset(skip)
            .limit(limit)
            .where(self.model.elastic_id.in_(list_ids))
        )
        return response.scalars().all()

    async def get_by_elastic_ids_paginated(
        self,
        *,
        params: Params | None = Params(),
        query: T | Select[T] | None = None,
        db_session: AsyncSession | None = None,
    ) -> Page[ModelType]:
        db_session = db_session or self.db.session
        if query is None:
            query = select(self.model)

        output = await paginate(db_session, query, params)
        return output

    async def get_group_by_name(
        self, *, name: str, db_session: AsyncSession | None = None
    ) -> TextData:
        db_session = db_session or super().get_db().session
        group = await db_session.execute(select(TextData).where(TextData.name == name))
        return group.scalar_one_or_none()


text_data = CRUDTextData(TextData)
