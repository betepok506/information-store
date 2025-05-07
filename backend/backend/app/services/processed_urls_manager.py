from sqlmodel.ext.asyncio.session import AsyncSession
from elasticsearch import AsyncElasticsearch
from fastapi_pagination import Page

from backend.app import crud
from backend.app.schemas.processed_urls_schema import (
    IProcessedUrlsResponse,
    IPorcessedUrlsReadFull,
)
from backend.app.models.processed_urls_model import ProcessedUrls
from backend.app.utils.exceptions import (
    ProcessedUrlNotFoundException,
)


class ProcessedUrlsManager:
    """Класс, реализует сервисную логику взаимодействия с таблицей Processed_url"""

    def __init__(self, db: AsyncSession, es: AsyncElasticsearch | None = None):
        self.db = db
        self.es = es

    async def get_processed_urls(self, params) -> Page[IProcessedUrlsResponse]:
        '''Функция для постраничного запроса обработанных url'''
        processed_urls = await crud.processed_urls.get_multi_paginated(
            db_session=self.db, params=params
        )
        new_items = []
        for cur_url in processed_urls.items:
            source_name = cur_url.source.name if not cur_url.source is None else None

            new_items.append(
                IProcessedUrlsResponse(
                    url=cur_url.url, id=cur_url.id, source_name=source_name
                )
            )
        processed_urls.items = new_items
        return processed_urls

    async def get_processed_url_by_url(self, url: str) -> IPorcessedUrlsReadFull:
        '''Функция для получения url по его имени'''
        processed_url_obj = await crud.processed_urls.get_by_url(
            db_session=self.db, url=url
        )
        if not processed_url_obj:
            raise ProcessedUrlNotFoundException(ProcessedUrls, url=url)
        return processed_url_obj

    async def _execute_in_transaction(self, operation, *args, **kwargs):
        """Выполняет операцию в контексте существующей транзакции"""
        if self.db.in_transaction():
            return await operation(*args, **kwargs)

        async with self.db.begin():
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                await self.db.rollback()
                raise
