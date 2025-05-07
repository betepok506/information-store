from elasticsearch.exceptions import RequestError

from backend.app.api.deps import get_elasticsearch_client
from backend.app.core.config import settings


async def create_indexes():
    es = await get_elasticsearch_client()
    if await es.indices.exists(index=settings.ELASTIC_VECTOR_INDEX):
        print(f"Индекс {settings.ELASTIC_VECTOR_INDEX} существует")
    else:
        try:
            await es.indices.create(
                index=settings.ELASTIC_VECTOR_INDEX,
                body={
                    "mappings": {
                        "properties": {
                            "vector": {
                                "type": "dense_vector",
                                "dims": settings.ELASTIC_VECTOR_DIMS,
                            },
                        }
                    }
                },
            )
        except RequestError as e:
            print(f"Ошибка создания индексов: {e}")
