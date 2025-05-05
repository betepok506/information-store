# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from app.models.message import Message
# from app.schemas.message import MessageCreate

# class MessageService:
#     def __init__(self, db: AsyncSession):
#         self.db = db

#     async def create_message(self, message: MessageCreate):
#         db_message = Message(**message.dict())
#         self.db.add(db_message)
#         await self.db.commit()
#         await self.db.refresh(db_message)
#         return db_message

#     async def get_messages(self, skip: int = 0, limit: int = 100):
#         result = await self.db.execute(
#             select(Message).offset(skip).limit(limit)
#         return result.scalars().all()