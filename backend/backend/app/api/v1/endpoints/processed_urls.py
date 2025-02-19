from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_pagination import Params

from backend.app import crud
# from backend.app.api import deps
from backend.app.utils.prepare_str import get_suf
from backend.app.models.processed_urls_model import ProcessedUrls
from backend.app.models.source_model import Source
from sqlmodel import SQLModel, func, select
from backend.app.schemas.processed_urls_schema import (
    IProcessedUrlsCreate,
    IProcessedUrlsUpdate,
    IProcessedUrlsRead,
    IProcessedUrlsResponse
)
from backend.app.schemas.response_schema import (
    IDeleteResponseBase,
    IGetResponseBase,
    IGetResponsePaginated,
    IPostResponseBase,
    IPutResponseBase,
    create_response,
)
from backend.app.schemas.text_data_schema import (  # IListTextDataCreate,; IGroupReadWithUsers,
    ITextDataCreate,
    ITextDataRead,
    ITextDataRequest,
    ITextDataUpdate,
    ITextDataUpdateRequest,
)

# from backend.app.schemas.role_schema import IRoleEnum
from backend.app.utils.exceptions import (
    IdNotFoundException,
    NameExistException,
    UrlValidationError,
    NameNotFoundException,
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
        suf_url = cur_url.suf_url
        
        prefix_url = cur_url.source.url if not cur_url.source is None else None
        source_name = cur_url.source.name if not cur_url.source is None else None
        url = None
        if not prefix_url is None and not suf_url is None:
            url=prefix_url+suf_url
        
        print(f'!!!! {url}')
        new_items.append(IProcessedUrlsResponse(url=url,
                                                id=cur_url.id,
                                                source_name=source_name))
    processed_urls.items = new_items
    return create_response(data=processed_urls)