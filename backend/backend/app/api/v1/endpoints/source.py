from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi_pagination import Params

from backend.app import crud
from backend.app.models.source_model import Source
from backend.app.schemas.response_schema import (
    IDeleteResponseBase,
    IGetResponseBase,
    IGetResponsePaginated,
    IPostResponseBase,
    create_response,
)
from backend.app.schemas.source_schema import ISourceCreate, ISourceRead, ISourceUpdate
from backend.app.utils.exceptions import (
    ContentNoChangeException,
    IdNotFoundException,
    NameExistException,
)

router = APIRouter()


@router.get("")
async def get_sources_list(
    params: Params = Depends(),
) -> IGetResponsePaginated[ISourceRead]:
    """
    Gets a paginated list of sources
    """
    sources = await crud.source.get_multi_paginated(params=params)
    print("sources", sources)
    return create_response(data=sources)


@router.get("/{source_id}")
async def get_source_id(
    source_id: UUID,
) -> IGetResponseBase[ISourceRead]:
    """
    Gets a source by its id
    """
    source = await crud.source.get(id=source_id)
    if not source:
        raise IdNotFoundException(Source, id=source_id)
    return create_response(data=source)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_source(
    source: ISourceCreate,
) -> IPostResponseBase[ISourceRead]:
    """
    Creates a new source
    """
    source_current = await crud.source.get_source_by_name(name=source.name)
    if source_current:
        raise NameExistException(Source, name=source_current.name)

    source = await crud.source.create(obj_in=source)
    return create_response(data=source)


@router.put("/{source_id}")
async def update_source(
    source_id: UUID,
    new_source: ISourceUpdate,
) -> IPostResponseBase[ISourceRead]:
    """
    Update a source by its id

    Required roles:
    - admin
    - manager
    """
    current_source = await crud.source.get(id=source_id)
    if not current_source:
        raise IdNotFoundException(Source, id=source_id)

    if current_source.name == new_source.name and current_source.url == new_source.url:
        raise ContentNoChangeException(detail="The content has not changed")
    # TODO: Проверить условия обновления элемента
    exist_source = await crud.source.get_source_by_name(name=new_source.name)
    if exist_source:
        raise NameExistException(Source, name=exist_source.name)

    heroe_updated = await crud.source.update(
        obj_current=current_source, obj_new=new_source
    )
    return create_response(data=heroe_updated)


@router.delete("/{source_id}")
async def remove_source(
    source_id: UUID,
) -> IDeleteResponseBase[ISourceRead]:
    """
    Deletes a source by its id

    Required roles:
    - admin
    - manager
    """
    current_source = await crud.source.get(id=source_id)
    if not current_source:
        raise IdNotFoundException(Source, id=source_id)
    
    source = await crud.source.remove(id=source_id)
    return create_response(data=source)
