from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends
from fastapi_pagination import Params
from backend.app import crud
from backend.app.api import deps

# from backend.app.deps import group_deps, user_deps
from backend.app.models.text_data_model import TextData
from backend.app.models.source_model import Source
from backend.app.models.processed_urls_model import ProcessedUrls
from backend.app.schemas.text_data_schema import (
    ITextDataCreate,
    ITextDataRead,
    ITextDataRequest,
    ITextDataUpdateRequest,
    # IListTextDataCreate,
    # IGroupReadWithUsers,
    ITextDataUpdate,
)
from backend.app.utils.hash import get_hash
from backend.app.schemas.processed_urls_schema import (
    IProcessedUrlsCreate,
    IProcessedUrlsUpdate,
)
from backend.app.schemas.response_schema import (
    IGetResponseBase,
    IDeleteResponseBase,
    IGetResponsePaginated,
    IPostResponseBase,
    IPutResponseBase,
    create_response,
)

# from backend.app.schemas.role_schema import IRoleEnum
from backend.app.utils.exceptions import (
    IdNotFoundException,
    NameExistException,
    NameNotFoundException,
)

router = APIRouter()


@router.get("")
async def get_text_data(
    params: Params = Depends(),
    # current_user: User = Depends(deps.get_current_user()),
) -> IGetResponsePaginated[ITextDataRead]:
    """
    Gets a paginated list of groups
    """
    groups = await crud.text_data.get_multi_paginated(params=params)
    return create_response(data=groups)


@router.get("/{text_data_id}")
async def get_text_data_by_id(
    text_data_id: UUID,
    # current_user: User = Depends(deps.get_current_user()),
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


@router.post("")
async def create_text_data(
    obj_in: ITextDataRequest,
    # source : Source = Depends (
    # )
    # current_user: User = Depends(
    #     deps.get_current_user(required_roles=[IRoleEnum.admin, IRoleEnum.manager])
    # ),
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
    # text_data_current = await crud.text_data.get_text_data_by_name(name=text_data.name)
    source = await crud.source.get_source_by_name(name=obj_in.source_name)
    if not source:
        raise NameNotFoundException(Source, name=obj_in.source_name)

    hashed_str = get_hash(obj_in.text)
    processed_url = IProcessedUrlsCreate(
        suf_url=obj_in.url, source_by_id=source.id, hash=hashed_str
    )
    new_processed_url = await crud.processed_urls.create(obj_in=processed_url)
    # if text_data_current:
    # raise NameExistException(TextData, name=group.name)
    text_data = ITextDataCreate(
        text=obj_in.text,
        elastic_id=obj_in.elastic_id,
        processed_urls_by_id=new_processed_url.id,
    )

    print(text_data)
    new_text_data = await crud.text_data.create(obj_in=text_data)
    return create_response(data=new_text_data)


# @router.post("")
# async def create_list_text_data(
#     obj_in: List[ITextDataCreate],
#     # source : Source = Depends (

#     # )
#     # current_user: User = Depends(
#     #     deps.get_current_user(required_roles=[IRoleEnum.admin, IRoleEnum.manager])
#     # ),
# ) -> IPostResponseBase[ITextDataRead]:
#     """
#     Creates a new group

#     {
#         "text": "ssssssssssfdsfgsdgdgdgsfgsfg",
#         "elastic_id": "string",
#         "url": "http://localhost:222/api/v1/endpoints",
#         "source_name": "string22"
#     }
#     """
#     # text_data_current = await crud.text_data.get_text_data_by_name(name=text_data.name)
#     source = await crud.source.get_source_by_name(name=obj_in.source_name)
#     if not source:
#         raise NameNotFoundException(Source, name=obj_in.source_name)

#     print(get_hash(obj_in.text))
#     hashed_str = get_hash(obj_in.text)
#     processed_url = IProcessedUrlsCreate(suf_url=obj_in.url,
#                                          source_by_id=source.id,
#                                          hash=hashed_str)
#     new_processed_url = await crud.processed_urls.create(obj_in=processed_url)
#     # if text_data_current:
#         # raise NameExistException(TextData, name=group.name)
#     text_data = ITextDataCreate(text=obj_in.text,
#                                 elastic_id=obj_in.elastic_id,
#                                 processed_urls_by_id=new_processed_url.id)

#     print(text_data)
#     new_text_data = await crud.text_data.create(obj_in=text_data)
#     return create_response(data=new_text_data)


@router.put("/{text_data_id}")
async def update_text_data(
    obj_in: ITextDataUpdateRequest,
    text_data_id: str,
    # current_group: TextData = Depends(group_deps.get_group_by_id), # TODO: Сделать зависимость для запроса текущих данных по id
    # current_user: User = Depends(
    #     deps.get_current_user(required_roles=[IRoleEnum.admin, IRoleEnum.manager])
    # ),
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
        id=cur_text_data.processed_urls_by_id
    )
    if not current_processed_url:
        raise IdNotFoundException(ProcessedUrls, id=cur_text_data.processed_urls_by_id)

    hashed_str = None
    if not obj_in.text is None:
        hashed_str = get_hash(obj_in.text)

    processed_urls_params = {
        "suf_url": obj_in.url,
        "hash": hashed_str,
        "source_by_id": source.id,
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
        processed_urls_by_id=updated_processed_url.id,
    )

    updated_text_data = await crud.text_data.update(
        obj_current=cur_text_data, obj_new=updated_text_data
    )
    return create_response(data=updated_text_data)


@router.delete("/{text_data_id}")
async def remove_text_data(
    text_data_id: UUID,
    # current_user: User = Depends(
    #     deps.get_current_user(required_roles=[IRoleEnum.admin, IRoleEnum.manager])
    # ),
) -> IDeleteResponseBase[ITextDataRead]:
    """
    Deletes a text data by its id
    """
    current_text_data = await crud.text_data.get(id=text_data_id)
    if not current_text_data:
        raise IdNotFoundException(TextData, id=text_data_id)
    
    team = await crud.text_data.remove(id=text_data_id)
    return create_response(data=team)


# @router.post("/add_user/{user_id}/{group_id}")
# async def add_user_into_a_group(
#     user: User = Depends(user_deps.is_valid_user),
#     group: Group = Depends(group_deps.get_group_by_id),
#     # current_user: User = Depends(
#     #     deps.get_current_user(required_roles=[IRoleEnum.admin, IRoleEnum.manager])
#     # ),
# ) -> IPostResponseBase[IGroupRead]:
#     """
#     Adds a user into a group

#     Required roles:
#     - admin
#     - manager
#     """
#     group = await crud.group.add_user_to_group(user=user, group_id=group.id)
#     return create_response(message="User added to group", data=group)
