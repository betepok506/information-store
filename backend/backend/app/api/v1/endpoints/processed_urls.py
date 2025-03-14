from fastapi import APIRouter, Depends
from fastapi_pagination import Params

from backend.app import crud
from backend.app.models.processed_urls_model import ProcessedUrls
from backend.app.schemas.processed_urls_schema import (
    IProcessedUrlsResponse,
    IPorcessedUrlsReadFull,
)
from backend.app.schemas.response_schema import (
    IGetResponseBase,
    IGetResponsePaginated,
    create_response,
)
from backend.app.utils.exceptions import (
    ProcessedUrlNotFoundException,
)

router = APIRouter()


@router.get("")
async def get_processed_urls(
    params: Params = Depends(),
) -> IGetResponsePaginated[IProcessedUrlsResponse]:
    """
    Gets a paginated list of processed urls
    """
    processed_urls = await crud.processed_urls.get_multi_paginated(params=params)
    new_items = []
    for cur_url in processed_urls.items:
        source_name = cur_url.source.name if not cur_url.source is None else None

        new_items.append(
            IProcessedUrlsResponse(
                url=cur_url.url, id=cur_url.id, source_name=source_name
            )
        )
    processed_urls.items = new_items
    return create_response(data=processed_urls)


@router.get("/check")
async def get_processed_url_by_url(
    url: str,
) -> IGetResponseBase[IPorcessedUrlsReadFull]:
    """
    Запрос URL
    """
    processed_url_obj = await crud.processed_urls.get_by_url(url=url)
    if not processed_url_obj:
        raise ProcessedUrlNotFoundException(ProcessedUrls, url=url)

    return create_response(data=processed_url_obj)
