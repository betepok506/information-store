# from backend.app.models.group_model import Group
# from backend.app.models.user_model import User
from sqlmodel import select

# from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.app.crud.base_crud import CRUDBase
from backend.app.models.text_data_model import TextData

# from backend.app.schemas.group_schema import IGroupCreate, IGroupUpdate
from backend.app.schemas.text_data_schema import ITextDataCreate, ITextDataUpdate


class CRUDTextData(CRUDBase[TextData, ITextDataCreate, ITextDataUpdate]):
    async def get_group_by_name(
        self, *, name: str, db_session: AsyncSession | None = None
    ) -> TextData:
        db_session = db_session or super().get_db().session
        group = await db_session.exec(select(TextData).where(TextData.name == name))
        return group.scalar_one_or_none()


text_data = CRUDTextData(TextData)
