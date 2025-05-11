from typing import Any, Generic, TypeVar
from uuid import UUID

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlmodel import paginate
from pydantic import BaseModel
from sqlmodel import SQLModel, func, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import Select

from app.schemas import IOrderEnum

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
SchemaType = TypeVar("SchemaType", bound=BaseModel)
T = TypeVar("T", bound=SQLModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]):
        """
        CRUD object with default methods to Create,
        Read, Update, Delete (CRUD).

        **Parameters**
        * `model`: A SQLModel model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get(
        self, *, db_session: AsyncSession, id: UUID | str
    ) -> ModelType | None:
        query = select(self.model).where(self.model.id == id)
        response = await db_session.execute(query)
        return response.scalar_one_or_none()

    async def get_by_ids(
        self,
        *,
        db_session: AsyncSession,
        list_ids: list[UUID | str],
    ) -> list[ModelType] | None:
        response = await db_session.execute(
            select(self.model).where(self.model.id.in_(list_ids))
        )
        return response.scalars().all()

    async def get_count(self, db_session: AsyncSession) -> ModelType | None:
        response = await db_session.execute(
            select(func.count()).select_from(select(self.model).subquery())
        )
        return response.scalar_one()

    async def get_multi(
        self,
        *,
        db_session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        query: T | Select[T] | None = None,
    ) -> list[ModelType]:
        if query is None:
            query = (
                select(self.model)
                .offset(skip)
                .limit(limit)
                .order_by(self.model.id)
            )
        response = await db_session.execute(query)
        return response.scalars().all()

    async def get_multi_paginated(
        self,
        *,
        db_session: AsyncSession,
        params: Params | None = Params(),
        query: T | Select[T] | None = None,
    ) -> Page[ModelType]:
        if query is None:
            query = select(self.model)

        output = await paginate(db_session, query, params)
        return output

    async def get_multi_paginated_ordered(
        self,
        *,
        db_session: AsyncSession,
        params: Params | None = Params(),
        order_by: str | None = None,
        order: IOrderEnum | None = IOrderEnum.ascendent,
        query: T | Select[T] | None = None,
    ) -> Page[ModelType]:
        columns = self.model.__table__.columns

        if order_by is None or order_by not in columns:
            order_by = "id"

        if query is None:
            if order == IOrderEnum.ascendent:
                query = select(self.model).order_by(columns[order_by].asc())
            else:
                query = select(self.model).order_by(columns[order_by].desc())

        return await paginate(db_session, query, params)

    async def get_multi_ordered(
        self,
        *,
        db_session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        order: IOrderEnum | None = IOrderEnum.ascendent,
    ) -> list[ModelType]:
        # db_session = db_session or self.db.session

        columns = self.model.__table__.columns

        if order_by is None or order_by not in columns:
            order_by = "id"

        if order == IOrderEnum.ascendent:
            query = (
                select(self.model)
                .offset(skip)
                .limit(limit)
                .order_by(columns[order_by].asc())
            )
        else:
            query = (
                select(self.model)
                .offset(skip)
                .limit(limit)
                .order_by(columns[order_by].desc())
            )

        response = await db_session.execute(query)
        return response.scalars().all()

    async def create(
        self,
        *,
        db_session: AsyncSession,
        obj_in: CreateSchemaType | ModelType,
        created_by_id: UUID | str | None = None,
    ) -> ModelType:
        db_obj = self.model.model_validate(obj_in)  # type: ignore

        if created_by_id:
            db_obj.created_by_id = created_by_id
        db_session.add(db_obj)
        await db_session.flush()
        await db_session.refresh(db_obj)
        return db_obj

    async def create_many(
        self,
        *,
        db_session: AsyncSession,
        obj_in: list[CreateSchemaType | ModelType],
        created_by_id: UUID | str | None = None,
    ) -> list[ModelType]:
        data = [self.model.model_validate(obj).dict() \
            for obj in obj_in]  # type: ignore

        if created_by_id:
            for item in data:
                item["created_by_id"] = created_by_id

        await db_session.bulk_insert_mappings(self.model, data)
        await db_session.flush()
        return [self.model(**item) for item in data]

    async def update(
        self,
        *,
        db_session: AsyncSession,
        obj_current: ModelType,
        obj_new: UpdateSchemaType | dict[str, Any] | ModelType,
    ) -> ModelType:

        if isinstance(obj_new, dict):
            update_data = obj_new
        else:
            update_data = obj_new.model_dump(exclude_none=True)
        for field in update_data:
            setattr(obj_current, field, update_data[field])

        db_session.add(obj_current)
        await db_session.flush()
        await db_session.refresh(obj_current)
        return obj_current

    async def remove(
        self, *, db_session: AsyncSession, id: UUID | str
    ) -> ModelType:
        response = await db_session.execute(
            select(self.model).where(self.model.id == id)
        )
        obj = response.scalar_one()
        await db_session.delete(obj)
        await db_session.flush()
        return obj
