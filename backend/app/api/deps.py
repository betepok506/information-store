from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from elasticsearch import AsyncElasticsearch
from prometheus_client import Counter, Histogram
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.db.session import SessionLocal

request_count = Counter("http_requests_total", "Total number of requests")
request_latency = Histogram(
    "http_request_duration_seconds", "Request latency in seconds"
)
http_404_counter = Counter(
    "http_404_errors_total", "Total number of 404 errors"
)
http_502_counter = Counter(
    "http_502_errors_total", "Total number of 502 errors"
)
http_500_counter = Counter(
    "http_500_errors_total", "Total number of 500 errors"
)
http_200_counter = Counter(
    "http_200_errors_total", "Total number of 200 response"
)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


class ElasticsearchClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AsyncElasticsearch(
                hosts=[settings.ELASTIC_SEARCH_DATABASE_URI]
            )
        return cls._instance


async def get_elasticsearch_client():
    return ElasticsearchClient.get_instance()
