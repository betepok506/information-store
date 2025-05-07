from fastapi import APIRouter, Depends, Response
from fastapi_pagination import Params
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db
from backend.app.schemas.processed_urls_schema import (
    IProcessedUrlsResponse,
    IPorcessedUrlsReadFull,
)
from backend.app.schemas.response_schema import (
    IGetResponseBase,
    IGetResponsePaginated,
    create_response,
)
from backend.app.services import ProcessedUrlsManager

router = APIRouter()


@router.get("")
async def get_processed_urls(
    params: Params = Depends(),
    db: AsyncSession = Depends(get_db)
) -> IGetResponsePaginated[IProcessedUrlsResponse]:
    """
    Gets a paginated list of processed urls
    """
    async with db as session:  
        service = ProcessedUrlsManager(db=session)
        try:
            result = await service.get_processed_urls(params=params)
        except Exception as e:
            return Response(f"Internal server error. Error: {e}", status_code=500)
    return create_response(data=result)


@router.get("/check")
async def get_processed_url_by_url(
    url: str,
    db: AsyncSession = Depends(get_db)
) -> IGetResponseBase[IPorcessedUrlsReadFull]:
    """
    Запрос URL
    """
    async with db as session:  
        service = ProcessedUrlsManager(db=session)
        try:
            result = await service.get_processed_url_by_url(url=url)
        except Exception as e:
            return Response(f"Internal server error. Error: {e}", status_code=500)
    return create_response(data=result)
