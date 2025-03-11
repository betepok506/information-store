from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.crud.base_crud import CRUDBase
from backend.app.models.processed_urls_model import ProcessedUrls
from backend.app.schemas.processed_urls_schema import (
    IProcessedUrlsCreate,
    IProcessedUrlsUpdate,
)


class CRUDProcessedUrls(
    CRUDBase[ProcessedUrls, IProcessedUrlsCreate, IProcessedUrlsUpdate]
):
    async def get_by_hash(
        self, *, hash: str, db_session: AsyncSession | None = None
    ) -> ProcessedUrls | None:
        db_session = db_session or super().get_db().session
        processed_url = await db_session.exec(
            select(ProcessedUrls).where(ProcessedUrls.hash == hash)
        )
        return processed_url.scalar_one_or_none()

    async def get_by_url(
        self, *, url: str, db_session: AsyncSession | None = None
    ) -> ProcessedUrls | None:
        db_session = db_session or super().get_db().session
        processed_url = await db_session.execute(
            select(ProcessedUrls).where(ProcessedUrls.url == url)
        )
        return processed_url.scalar_one_or_none()


processed_urls = CRUDProcessedUrls(ProcessedUrls)
