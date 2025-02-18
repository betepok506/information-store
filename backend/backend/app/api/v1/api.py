from fastapi import APIRouter

from backend.app.api.v1.endpoints import source, text_data

api_router = APIRouter()
api_router.include_router(source.router, prefix="/source", tags=["source"])
api_router.include_router(text_data.router, prefix="/text_data", tags=["text_data"])
