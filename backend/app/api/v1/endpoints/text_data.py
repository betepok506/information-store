from typing import List
from uuid import UUID

from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends, Response
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.api.deps import get_db, get_elasticsearch_client
from app.core.config import settings
from app.models import TextData
from app.schemas import (
    IDeleteResponseBase,
    IGetResponseBase,
    IGetResponsePaginated,
    IPostResponseBase,
    IPutResponseBase,
    ITextDataCreateRequest,
    ITextDataReadBasic,
    ITextDataReadFull,
    ITextDataUpdateRequest,
    create_response,
)
from app.services import TextDataManager
from app.utils.exceptions import IdNotFoundException, APIException
from app.schemas import ErrorCode
from fastapi import  status

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
            return create_response(data=None, 
                                   message=f"Internal server error. Error: {e}")
    return create_response(data=result)


@router.get("/{text_data_id}")
async def get_text_data_by_id(
    text_data_id: UUID, db: AsyncSession = Depends(get_db)
) -> IGetResponseBase[ITextDataReadBasic]:
    """Gets a group by its id"""
    async with db as session:
        service = TextDataManager(db=session)
        try:
            result = await service.get_text_data_by_id(
                text_data_id=text_data_id
            )
        except Exception as e:
            return Response(
                f"Internal server error. Error: {e}", status_code=500
            )

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
            return Response(
                f"Internal server error. Error: {e}", status_code=500
            )

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
    print(f"db_session 11 : {type(db)}")
    async with db as session:
        print(f"db_session 2 : {type(session)}")
        service = TextDataManager(db=session, es=es)
        try:
            result = await service.create_text_data(
                obj_in, settings.ELASTIC_VECTOR_INDEX
            )
        except Exception as e:
            raise APIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                details=[{"field": "exception", "message": str(e)}]
            )
            
        return create_response(data=result)
    
    # async with db as session:
    #     service = TextDataManager(db=session, es=es)
    #     try:
    #         result = await service.create_text_data(
    #             obj_in, settings.ELASTIC_VECTOR_INDEX
    #         )
    #     except Exception as e:
    #         raise APIException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             error_code=ErrorCode.INTERNAL_ERROR,
    #             message="Internal server error",
    #             details=[{"field": "exception", "message": str(e)}]
    #         )
            
    #     return create_response(data=result)


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
            return Response(
                f"Internal server error. Error: {e}", status_code=500
            )
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
