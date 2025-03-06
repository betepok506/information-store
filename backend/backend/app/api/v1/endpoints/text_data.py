from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Params

from backend.app import crud
from backend.app.utils.prepare_str import get_suf
from backend.app.models.processed_urls_model import ProcessedUrls
from backend.app.models.source_model import Source
from sqlmodel import SQLModel, func, select
from backend.app.models.text_data_model import TextData
from backend.app.schemas.processed_urls_schema import (
    IProcessedUrlsCreate,
    IProcessedUrlsUpdate,
)
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
    ITextDataRead,
    ITextDataRequest,
    ITextDataUpdate,
    ITextDataUpdateRequest,
)
from backend.app.utils.exceptions import (
    IdNotFoundException,
    NameExistException,
    UrlValidationError,
    NameNotFoundException,
)
from backend.app.utils.prepare_str import get_suf
from backend.app.utils.hash import get_hash

router = APIRouter()


@router.get("")
async def get_text_data(
    params: Params = Depends(),
) -> IGetResponsePaginated[ITextDataRead]:
    """
    Gets a paginated list of groups
    """
    groups = await crud.text_data.get_multi_paginated(params=params)
    print(f"{groups=}")
    return create_response(data=groups)


@router.get("/{text_data_id}")
async def get_text_data_by_id(
    text_data_id: UUID,
) -> IGetResponseBase[ITextDataRead]:
    """
    Gets a group by its id
    """
    text_data = await crud.text_data.get(id=text_data_id)
    print(text_data)
    if text_data:
        return create_response(data=text_data)
    else:
        raise IdNotFoundException(TextData, text_data)


# @router.post("/elastic_ids/")
# async def get_text_data_by_id(
#     elastic_ids: List[str],
#     skip: int = 0,
#     limit: int = 100,
#     # current_user: User = Depends(deps.get_current_user()),
# ) -> IPostResponseBase[List[ITextDataRead]]:
#     """
#     Gets a text data by its elastic ids
#     """
#     text_data = await crud.text_data.get_by_elastic_ids(
#         list_ids=elastic_ids, skip=skip, limit=limit
#     )
#     if text_data:
#         return create_response(data=text_data)
#     else:
#         raise IdNotFoundException(TextData, text_data)


@router.post("/elastic_ids/")
async def get_text_data_by_elastic_ids_paginated(
    elastic_ids: List[str],
    params: Params = Depends(),
) -> IGetResponsePaginated[ITextDataRead]:
    """
    Gets a text data by its elastic search indexes
    """
    query = select(TextData).where(TextData.elastic_id.in_(elastic_ids))
    text_data = await crud.text_data.get_by_elastic_ids_paginated(
        query=query, params=params
    )

    if text_data:
        return create_response(data=text_data)
    else:
        raise IdNotFoundException(TextData, text_data)


@router.post("")
async def create_text_data(
    obj_in: ITextDataRequest,
) -> IPostResponseBase[ITextDataRead]:
    """
    Creates a new group

    {
        "text": "ssssssssssfdsfgsdgdgdgsfgsfg",
        "elastic_id": "string",
        "url": "http://localhost:222/api/v1/endpoints",
        "source_name": "string22"
    }
    """
    source = await crud.source.get_source_by_name(name=obj_in.source_name)
    if not source:
        raise NameNotFoundException(Source, name=obj_in.source_name)

    hashed_str = get_hash(obj_in.text)
    if len(obj_in.url) < len(source.url):
        raise UrlValidationError(ProcessedUrls)

    suf_url = get_suf(obj_in.url, source.url)
    processed_url = IProcessedUrlsCreate(
        suf_url=suf_url, source_id=source.id, hash=hashed_str
    )
    new_processed_url = await crud.processed_urls.create(obj_in=processed_url)
    text_data = ITextDataCreate(
        text=obj_in.text,
        elastic_id=obj_in.elastic_id,
        processed_urls_id=new_processed_url.id,
    )

    print(text_data)
    new_text_data = await crud.text_data.create(obj_in=text_data)
    return create_response(data=new_text_data)


@router.put("/{text_data_id}")
async def update_text_data(
    obj_in: ITextDataUpdateRequest,
    text_data_id: str,
) -> IPutResponseBase[ITextDataRead]:
    """
    Updates a text data by its id

    """
    cur_text_data = await crud.text_data.get(id=text_data_id)
    if not cur_text_data:
        raise IdNotFoundException(TextData, cur_text_data)

    source = await crud.source.get_source_by_name(name=obj_in.source_name)
    if not source:
        raise IdNotFoundException(Source, id=text_data_id)

    current_processed_url = await crud.processed_urls.get(
        id=cur_text_data.processed_urls_id
    )
    if not current_processed_url:
        raise IdNotFoundException(ProcessedUrls, id=cur_text_data.processed_urls_id)

    hashed_str = None
    if not obj_in.text is None:
        hashed_str = get_hash(obj_in.text)

    if len(obj_in.url) < len(source.url):
        raise UrlValidationError(ProcessedUrls)

    suf_url = get_suf(obj_in.url, source.url)

    processed_urls_params = {
        "suf_url": suf_url,
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
    updated_text_data = ITextDataUpdate(
        **{key: value for key, value in obj_in.__dict__.items() if value is not None},
        processed_urls_id=updated_processed_url.id,
    )

    updated_text_data = await crud.text_data.update(
        obj_current=cur_text_data, obj_new=updated_text_data
    )
    return create_response(data=updated_text_data)


@router.delete("/{text_data_id}")
async def remove_text_data(
    text_data_id: UUID,
) -> IDeleteResponseBase[ITextDataRead]:
    """
    Deletes a text data by its id
    """
    removed_text_data = await crud.text_data.remove(id=text_data_id)
    return create_response(data=removed_text_data)
