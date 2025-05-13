"""
Модуль для работы с обработанными URL-адресами.

Содержит классы для управления данными об обработанных URL, взаимодействия с БД
и обработки транзакций.
"""

from elasticsearch import AsyncElasticsearch
from fastapi_pagination import Page
from sqlmodel.ext.asyncio.session import AsyncSession

from app import crud
from app.models import ProcessedUrls
from app.schemas import IPorcessedUrlsReadFull, IProcessedUrlsResponse
from app.utils.exceptions import ProcessedUrlNotFoundException

__all__ = ["ProcessedUrlsManager"]


class ProcessedUrlsManager:
    """
    Менеджер для работы с обработанными URL.

    Обеспечивает взаимодействие с таблицей Processed_urls и связанными
    сервисами.

    Attributes
    ----------
    db : AsyncSession
        Асинхронная сессия SQLAlchemy для работы с БД
    es : AsyncElasticsearch | None
        Клиент Elasticsearch (необязательный)
    """

    def __init__(self, db: AsyncSession, es: AsyncElasticsearch | None = None):
        """
        Инициализация менеджера.

        Parameters:
            db : AsyncSession
                Асинхронная сессия SQLAlchemy
            es : AsyncElasticsearch | None
                Опциональный клиент Elasticsearch
        """
        self.db = db
        self.es = es

    async def get_processed_urls(self, params) -> Page[IProcessedUrlsResponse]:
        """
        Получает пагинированный список обработанных URL.

        Parameters
        ----------
        params : Params
            Параметры пагинации и фильтрации

        Returns
        -------
        Page[IProcessedUrlsResponse]
            Страница с результатами в формате IProcessedUrlsResponse

        Notes
        -----
        Автоматически добавляет имя источника для каждого URL.
        """
        processed_urls = await crud.processed_urls.get_multi_paginated(
            db_session=self.db, params=params
        )
        new_items = []
        for cur_url in processed_urls.items:
            source_name = (
                cur_url.source.name if cur_url.source is not None else None
            )

            new_items.append(
                IProcessedUrlsResponse(
                    url=cur_url.url, id=cur_url.id, source_name=source_name
                )
            )
        processed_urls.items = new_items
        return processed_urls

    async def get_processed_url_by_url(
        self, url: str
    ) -> IPorcessedUrlsReadFull:
        """
        Получает полную информацию об URL по его значению.

        Parameters
        ----------
        url : str
            Искомый URL

        Returns
        -------
        IPorcessedUrlsReadFull
            Полная информация об обработанном URL

        Raises
        ------
        ProcessedUrlNotFoundException
            Если URL не найден в базе данных
        """
        processed_url_obj = await crud.processed_urls.get_by_url(
            db_session=self.db, url=url
        )
        if not processed_url_obj:
            raise ProcessedUrlNotFoundException(ProcessedUrls, url=url)
        return processed_url_obj

    async def _execute_in_transaction(self, operation, *args, **kwargs):
        """
        Выполнение операции в транзакции.

        Parameters:
            operation : Callable
                Асинхронная функция для выполнения
            *args:
                Позиционные аргументы операции
            **kwargs:
                Именованные аргументы операции

        Returns:
            Any: Результат выполнения операции

        Raises:
            Exception: При ошибке выполнения с откатом транзакции
        """
        if self.db.in_transaction():
            return await operation(*args, **kwargs)

        async with self.db.begin():
            try:
                return await operation(*args, **kwargs)
            except Exception:
                await self.db.rollback()
                raise
