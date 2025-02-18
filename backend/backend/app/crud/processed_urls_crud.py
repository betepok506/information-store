# from backend.app.schemas.media_schema import IMediaCreate
# from backend.app.schemas.user_schema import IUserCreate, IUserUpdate
# from backend.app.models.user_model import User

# from backend.app.crud.user_follow_crud import user_follow as UserFollowCRUD
from sqlmodel import select

# from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession

# from backend.app.models.media_model import Media
# from backend.app.models.image_media_model import ImageMedia
# from backend.app.core.security import verify_password, get_password_hash
# from pydantic.networks import EmailStr
# from typing import Any
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


processed_urls = CRUDProcessedUrls(ProcessedUrls)
