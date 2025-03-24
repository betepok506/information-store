from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from fastapi_pagination import Params

from backend.app import crud
from backend.app.api.deps import get_db
from backend.app.models.processed_urls_model import ProcessedUrls
from backend.app.models.source_model import Source
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from elasticsearch import AsyncElasticsearch
from backend.app.api.deps import get_elasticsearch_client
from backend.app.models.text_data_model import TextData
from backend.app.schemas.processed_urls_schema import (
    IProcessedUrlsCreate,
    IProcessedUrlsUpdate,
)
from backend.app.utils.map_schema import merge_schemas
from backend.app.schemas.response_schema import (
    IDeleteResponseBase,
    IGetResponseBase,
    IGetResponsePaginated,
    IPostResponseBase,
    IPutResponseBase,
    create_response,
)
from backend.app.schemas.text_data_schema import (
    ITextDataCreate,
    ITextDataUpdate,
    ITextDataUpdateRequest,
    ITextDataCreateRequest,
    ITextDataReadBasic,
    ITextDataReadFull,
)
from backend.app.schemas.source_schema import ISourceCreate
from backend.app.utils.exceptions import (
    IdNotFoundException,
    SourceNotFoundException,
)
from backend.app.utils.hash import get_hash

router = APIRouter()


@router.get("")
async def get_text_data(
    params: Params = Depends(),
) -> IGetResponsePaginated[ITextDataReadBasic]:
    """
    Gets a paginated list of groups
    """
    query = (
        select(TextData, ProcessedUrls, Source)
        .join(
            ProcessedUrls, TextData.processed_urls_id == ProcessedUrls.id, isouter=True
        )
        .join(Source, ProcessedUrls.source_id == Source.id, isouter=True)
    )
    groups = await crud.text_data.get_multi_paginated(params=params, query=query)
    print(f"{groups=}")
    return create_response(data=groups)


@router.get("/{text_data_id}")
async def get_text_data_by_id(
    text_data_id: UUID,
    # current_user: User = Depends(deps.get_current_user()),
) -> IGetResponseBase[ITextDataReadBasic]:
    """
    Gets a group by its id
    """
    text_data = await crud.text_data.get(id=text_data_id)
    print(text_data)
    if text_data:
        return create_response(data=text_data)
    else:
        raise IdNotFoundException(TextData, text_data)


@router.post("/elastic_ids/")
async def get_text_data_by_elastic_ids_paginated(
    elastic_ids: List[str],
    params: Params = Depends(),
) -> IGetResponsePaginated[ITextDataReadBasic]:
    """
    Запрос текстов по индексам Elastic Search
    """
    query = (
        select(TextData, ProcessedUrls, Source)
        .join(
            ProcessedUrls, TextData.processed_urls_id == ProcessedUrls.id, isouter=True
        )
        .join(Source, ProcessedUrls.source_id == Source.id, isouter=True)
        .where(TextData.elastic_id.in_(elastic_ids))  # Фильтрация по массиву ID
    )
    text_data = await crud.text_data.get_by_elastic_ids_paginated(
        query=query, params=params
    )
    if text_data:
        return create_response(data=text_data)
    else:
        raise IdNotFoundException(TextData, text_data)


@router.post("")
async def create_text_data(
    obj_in: ITextDataCreateRequest,
    es: AsyncElasticsearch = Depends(get_elasticsearch_client),
) -> IPostResponseBase[ITextDataReadBasic]:
    """ """
    # TODO: Сделать транзакцию
    source = await crud.source.get_source_by_name(name=obj_in.source_name)
    if not source:
        # Если нет источника, создаем его
        # raise SourceNotFoundException(Source, source=obj_in.source_name)
        source = await crud.source.create(obj_in= ISourceCreate(name=obj_in.source_name, url=obj_in.url))

    hashed_str = get_hash(obj_in.text)
    processed_url = IProcessedUrlsCreate(
        url=obj_in.url, source_id=source.id, hash=hashed_str
    )
    new_processed_url = await crud.processed_urls.create(obj_in=processed_url)

    # Добавление вектора в Elastic Search
    try:
        item = await es.index(
            index="text_vectors",
            body={"text": "sdsdas", "vector": obj_in.vector},
        )
        print(f"{item['_id']=}")
        elastic_id = item["_id"]
    except Exception as e:
        return Response(f"Internal server error. Error: {e}", status_code=500)
    text_data = ITextDataCreate(
        text=obj_in.text,
        elastic_id=elastic_id,
        processed_urls_id=new_processed_url.id,
    )

    new_text_data = await crud.text_data.create(obj_in=text_data)
    return create_response(
        data=ITextDataReadFull(
            id=new_text_data.id,
            url=obj_in.url,
            # processed_urls=new_text_data.processed_urls,
            processed_urls_id=new_processed_url.id,
            text=new_text_data.text,
            elastic_id=new_text_data.elastic_id,
            vector=obj_in.vector,
        )
    )


@router.put("/{text_data_id}")
async def update_text_data(
    obj_in: ITextDataUpdateRequest,
    text_data_id: str,
    es: AsyncElasticsearch = Depends(get_elasticsearch_client),
    db_session: AsyncSession = Depends(get_db),
) -> IPutResponseBase[ITextDataReadFull]:
    """
    Updates a text data by its id

    """
    try:
        async with db_session.begin():
            cur_text_data = await crud.text_data.get_db_object(id=text_data_id)
            if not cur_text_data:
                raise IdNotFoundException(TextData, cur_text_data)

            current_processed_url = await crud.processed_urls.get(
                id=cur_text_data.processed_urls_id
            )
            if not current_processed_url:
                raise IdNotFoundException(
                    ProcessedUrls, id=cur_text_data.processed_urls_id
                )

            source = await crud.source.get(id=current_processed_url.source_id)
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
                obj_current=current_processed_url, obj_new=updated_processed_url
            )

            # Обновление вектора в Elastic Search
            elastic_id = None
            if obj_in.vector is not None:
                item = await es.update(
                    index="text_vectors",
                    id=cur_text_data.elastic_id,
                    body={
                        "doc": {  # Обязательный блок для update
                            "text": "sdsdas",
                            "vector": obj_in.vector,
                        }
                    },
                    # body={"text": "sdsdas", "vector": obj_in.vector},
                )
                elastic_id = item["_id"]

            response = await es.get(index="text_vectors", id=cur_text_data.elastic_id)
            vector = response.body["_source"]["vector"]

            updated_text_data = ITextDataUpdate()
            values = {
                "elastic_id": elastic_id,
                "processed_urls_id": updated_processed_url.id,
            }
            updated_text_data = merge_schemas(updated_text_data, obj_in, values)
            obj_updated_text_data = await crud.text_data.update(
                obj_current=cur_text_data, obj_new=updated_text_data
            )

            obj_response = ITextDataReadFull(
                id=obj_updated_text_data.id,
                text=obj_updated_text_data.text,
                elastic_id=obj_updated_text_data.elastic_id,
                url=updated_processed_url.url,
                processed_urls_id=updated_processed_url.id,
                vector=vector,
            )
            await db_session.commit()
            return create_response(data=obj_response)
    except Exception as e:
        # Откатываем транзакцию в случае ошибки
        await db_session.rollback()
        raise Response(f"Internal server error. Error: {e}", status_code=500)


@router.delete("/{text_data_id}")
async def remove_text_data(
    text_data_id: UUID,
) -> IDeleteResponseBase[ITextDataReadBasic]:
    """
    Deletes a text data by its id
    """
    removed_text_data = await crud.text_data.remove(id=text_data_id)
    # Удалить с ElasticSearch запись по индексу
    return create_response(data=removed_text_data)
