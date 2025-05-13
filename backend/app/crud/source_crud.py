from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Source
from app.schemas import ISourceCreate, ISourceUpdate

from .base_crud import CRUDBase

__all__ = ["source"]


class CRUDSource(CRUDBase[Source, ISourceCreate, ISourceUpdate]):
    async def get_by_name(
        self, *, db_session: AsyncSession, name: str
    ) -> Source:
        source = await db_session.execute(
            select(Source).where(Source.name == name)
        )
        return source.scalar_one_or_none()


source = CRUDSource(Source)
