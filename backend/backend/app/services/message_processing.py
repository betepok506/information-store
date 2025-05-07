from pydantic import ValidationError
from backend.app.schemas import ITextDataCreateRequest
from backend.app.api.deps import get_elasticsearch_client
from backend.app.services import TextDataManager
from backend.app.api.deps import get_db


class TextDataMessageProcessor:
    async def process_message(self, raw_data: dict):
        try:
            # Валидация через Pydantic схему
            obj_in = ITextDataCreateRequest(**raw_data)
            es = await get_elasticsearch_client()
            db = get_db()
            service = TextDataManager()
            async with db as session:
                result = await service.create_text_data(obj_in, es, session)
            return True
        except ValidationError as e:
            print(f"Validation error: {e}")
            return False