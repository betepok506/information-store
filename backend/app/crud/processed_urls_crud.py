from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import ProcessedUrls, Source
from app.schemas import (
    IPorcessedUrlsReadFull,
    IProcessedUrlsCreate,
    IProcessedUrlsUpdate,
)

from .base_crud import CRUDBase

__all__ = ["processed_urls"]


class CRUDProcessedUrls(
    CRUDBase[ProcessedUrls, IProcessedUrlsCreate, IProcessedUrlsUpdate]
):
    async def get_by_hash(
        self, *, db_session: AsyncSession, hash: str
    ) -> ProcessedUrls | None:
        processed_url = await db_session.exec(
            select(ProcessedUrls).where(ProcessedUrls.hash == hash)
        )
        return processed_url.scalar_one_or_none()

    async def get_by_url(
        self, *, db_session: AsyncSession, url: str
    ) -> IPorcessedUrlsReadFull | None:
        processed_url = await db_session.execute(
            select(ProcessedUrls, Source)
            .join(Source, ProcessedUrls.source_id == Source.id, isouter=True)
            .where(ProcessedUrls.url == url)
        )
        # TODO: ПРоверить если нет ни одного URL
        """
        TODO: Пока возвращаю первый элемент если он есть,
        в дальнейшем можно сделать поиск по похожести фрагмента
        """

        processed_url = processed_url.first()
        if processed_url is None:
            return None
        url, source = processed_url  # TODO: Пофиксить в случае None
        return IPorcessedUrlsReadFull(
            url=url.url, hash=url.hash, source_name=source.name
        )


processed_urls = CRUDProcessedUrls(ProcessedUrls)
