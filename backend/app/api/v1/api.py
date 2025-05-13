from fastapi import APIRouter

from app.api.v1.endpoints import (
    processed_urls,
    source,
    text_data,
    vectors,
)

api_router = APIRouter()
api_router.include_router(source.router, prefix="/source", tags=["source"])
api_router.include_router(text_data.router, prefix="/text", tags=["text"])
api_router.include_router(vectors.router, prefix="/vectors", tags=["vectors"])
api_router.include_router(
    processed_urls.router, prefix="/processed_urls", tags=["processed_urls"]
)
