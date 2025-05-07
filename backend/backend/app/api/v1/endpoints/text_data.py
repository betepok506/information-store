from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from fastapi_pagination import Params

# from fastapi_async_sqlalchemy import db
from backend.app import crud
from backend.app.api.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from elasticsearch import AsyncElasticsearch
from backend.app.api.deps import get_elasticsearch_client
from backend.app.models.text_data_model import TextData
from backend.app.services import TextDataManager
from backend.app.schemas.response_schema import (
    IDeleteResponseBase,
    IGetResponseBase,
    IGetResponsePaginated,
    IPostResponseBase,
    IPutResponseBase,
    create_response,
)
from backend.app.schemas.text_data_schema import (
    ITextDataUpdateRequest,
    ITextDataCreateRequest,
    ITextDataReadBasic,
    ITextDataReadFull,
)
from backend.app.utils.exceptions import (
    IdNotFoundException
)
from backend.app.core.config import settings

router = APIRouter()


@router.get("")
async def get_text_data(
    params: Params = Depends(), db: AsyncSession = Depends(get_db)
) -> IGetResponsePaginated[ITextDataReadBasic]:
    """
    Gets a paginated list of groups
    """
    async with db as session:
        service = TextDataManager(db=session)
        try:
            result = await service.get_text_data(params=params)
        except Exception as e:
            return Response(f"Internal server error. Error: {e}", status_code=500)
    return create_response(data=result)


@router.get("/{text_data_id}")
async def get_text_data_by_id(
    text_data_id: UUID, db: AsyncSession = Depends(get_db)
) -> IGetResponseBase[ITextDataReadBasic]:
    """
    Gets a group by its id
    """
    async with db as session:
        service = TextDataManager(db=session)
        try:
            result = await service.get_text_data_by_id(text_data_id=text_data_id)
        except Exception as e:
            return Response(f"Internal server error. Error: {e}", status_code=500)

    if result:
        return create_response(data=result)
    else:
        raise IdNotFoundException(TextData, result)


@router.post("/elastic_ids/")
async def get_by_elastic_ids_paginated(
    elastic_ids: List[str],
    params: Params = Depends(),
    db: AsyncSession = Depends(get_db),
) -> IGetResponsePaginated[ITextDataReadBasic]:
    """
    Запрос текстов по индексам Elastic Search
    """
    async with db as session:
        service = TextDataManager(db=session)
        try:
            result = await service.get_by_elastic_ids_paginated(
                elastic_ids=elastic_ids, params=params
            )
        except Exception as e:
            return Response(f"Internal server error. Error: {e}", status_code=500)

    if result:
        return create_response(data=result)
    else:
        raise IdNotFoundException(TextData, result)


@router.post("")
async def create_text_data(
    obj_in: ITextDataCreateRequest,
    db: AsyncSession = Depends(get_db),
    es: AsyncElasticsearch = Depends(get_elasticsearch_client),
) -> IPostResponseBase[ITextDataReadBasic]:
    """ """
    async with db as session:
        service = TextDataManager(db=session, es=es)
        try:
            result = await service.create_text_data(obj_in, settings.ELASTIC_VECTOR_INDEX)
        except Exception as e:
            return Response(f"Internal server error. Error: {e}", status_code=500)
        return create_response(data=result)


@router.put("/{text_data_id}")
async def update_text_data(
    obj_in: ITextDataUpdateRequest,
    text_data_id: str,
    es: AsyncElasticsearch = Depends(get_elasticsearch_client),
    db: AsyncSession = Depends(get_db),
) -> IPutResponseBase[ITextDataReadFull]:
    """
    Updates a text data by its id

    """
    async with db as session:
        service = TextDataManager(db=session, es=es)
        try:
            result = await service.update_text_data(
                obj_in, settings.ELASTIC_VECTOR_INDEX, text_data_id
            )
        except Exception as e:
            return Response(f"Internal server error. Error: {e}", status_code=500)
        return create_response(data=result)


@router.delete("/{text_data_id}")
async def remove_text_data(
    text_data_id: UUID,
) -> IDeleteResponseBase[ITextDataReadBasic]:
    """
    Deletes a text data by its id
    """
    removed_text_data = await crud.text_data.remove(id=text_data_id)
    # TODO: Удалить с ElasticSearch запись по индексу
    return create_response(data=removed_text_data)
