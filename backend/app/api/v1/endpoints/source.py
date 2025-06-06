from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas import (
    IDeleteResponseBase,
    IGetResponseBase,
    IGetResponsePaginated,
    IPostResponseBase,
    ISourceCreate,
    ISourceRead,
    ISourceUpdate,
    create_response,
)
from app.services import SourceManager

router = APIRouter()


@router.get("")
async def get_sources_list(
    params: Params = Depends(), db: AsyncSession = Depends(get_db)
) -> IGetResponsePaginated[ISourceRead]:
    """Gets a paginated list of sources"""
    async with db as session:
        service = SourceManager(db=session)
        try:
            result = await service.get_sources_list(params=params)
        except Exception as e:
            return Response(
                f"Internal server error. Error: {e}", status_code=500
            )
    return create_response(data=result)


@router.get("/{source_id}")
async def get_source_id(
    source_id: UUID, db: AsyncSession = Depends(get_db)
) -> IGetResponseBase[ISourceRead]:
    """
    Gets a source by its id
    """
    async with db as session:
        service = SourceManager(db=session)
        try:
            result = await service.get_source_id(source_id=source_id)
        except Exception as e:
            return Response(
                f"Internal server error. Error: {e}", status_code=500
            )
    return create_response(data=result)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_source(
    source: ISourceCreate, db: AsyncSession = Depends(get_db)
) -> IPostResponseBase[ISourceRead]:
    """
    Creates a new source
    """
    async with db as session:
        service = SourceManager(db=session)
        try:
            result = await service.create_source(obj_in=source)
        except Exception as e:
            return Response(
                f"Internal server error. Error: {e}", status_code=500
            )
    return create_response(data=result)


@router.put("/{source_id}")
async def update_source(
    source_id: UUID,
    new_source: ISourceUpdate,
    db: AsyncSession = Depends(get_db),
) -> IPostResponseBase[ISourceRead]:
    """
    Update a source by its id
    """
    async with db as session:
        service = SourceManager(db=session)
        try:
            result = await service.update_source(
                source_id=source_id, new_source=new_source
            )
        except Exception as e:
            return Response(
                f"Internal server error. Error: {e}", status_code=500
            )
    return create_response(data=result)


@router.delete("/{source_id}")
async def remove_source(
    source_id: UUID, db: AsyncSession = Depends(get_db)
) -> IDeleteResponseBase[ISourceRead]:
    """
    Deletes a source by its id
    """
    async with db as session:
        service = SourceManager(db=session)
        try:
            result = await service.remove_source(source_id=source_id)
        except Exception as e:
            return Response(
                f"Internal server error. Error: {e}", status_code=500
            )
    return create_response(data=result)


@router.get("/check/{name}")
async def check_source_by_name(
    name: str, db: AsyncSession = Depends(get_db)
) -> IGetResponseBase[ISourceRead]:
    """
    Запрос источника по его имени
    """
    async with db as session:
        service = SourceManager(db=session)
        try:
            result = await service.check_source_by_name(name=name)
        except Exception as e:
            return Response(
                f"Internal server error. Error: {e}", status_code=500
            )
    return create_response(data=result)
