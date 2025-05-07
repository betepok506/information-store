from pydantic import ValidationError
from backend.app.schemas import ITextDataCreateRequest
from backend.app.api.deps import get_elasticsearch_client
from backend.app.services import TextDataManager
from backend.app.api.deps import get_db
from backend.app.core.config import settings

class TextDataMessageProcessor:
    async def process_message(self, raw_data: dict):
        try:
            # Валидация через Pydantic схему
            obj_in = ITextDataCreateRequest(**raw_data)
            es = await get_elasticsearch_client()
            db = get_db()
            async with db as session:
                service = TextDataManager(db=session, es=es)
                result = await service.create_text_data(obj_in, settings.ELASTIC_VECTOR_INDEX)
            return True
        except ValidationError as e:
            print(f"Validation error: {e}")
            return False
