from pydantic import ValidationError

from app.api.deps import get_db, get_elasticsearch_client
from app.core.config import settings
from app.schemas import ITextDataCreateRequest

from .text_data_manager import TextDataManager

__all__ = ["TextDataMessageProcessor"]


class TextDataMessageProcessor:
    """Обработчик сообщений для текстовых данных."""

    async def process_message(self, raw_data: dict):
        """
        Обрабатывает входящее сообщение с текстовыми данными.

        Parameters
        ----------
        raw_data : dict
            Сырые данные сообщения

        Returns
        -------
        bool
            True если обработка прошла успешно, False при ошибке валидации

        Raises
        ------
        ValidationError
            Если данные не соответствуют ожидаемой схеме
        """
        try:
            # Валидация через Pydantic схему
            obj_in = ITextDataCreateRequest(**raw_data)
            es = await get_elasticsearch_client()
            db = get_db()
            async with db as session:
                service = TextDataManager(db=session, es=es)
                await service.create_text_data(
                    obj_in, settings.ELASTIC_VECTOR_INDEX
                )
            return True
        except ValidationError as e:
            print(f"Validation error: {e}")
            return False
