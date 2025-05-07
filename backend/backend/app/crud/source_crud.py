from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.crud.base_crud import CRUDBase
from backend.app.models.source_model import Source
from backend.app.schemas.source_schema import ISourceCreate, ISourceUpdate


class CRUDSource(CRUDBase[Source, ISourceCreate, ISourceUpdate]):
    async def get_by_name(
        self, *, db_session: AsyncSession, name: str
    ) -> Source:
        source = await db_session.execute(select(Source).where(Source.name == name))
        return source.scalar_one_or_none()


source = CRUDSource(Source)
