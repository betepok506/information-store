from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import redis.asyncio as aioredis
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.core.config import settings
from backend.app.db.session import SessionLocal

from prometheus_client import Counter, Histogram

request_count = Counter("http_requests_total", "Total number of requests")
request_latency = Histogram(
    "http_request_duration_seconds", "Request latency in seconds"
)
http_404_counter = Counter("http_404_errors_total", "Total number of 404 errors")
http_502_counter = Counter("http_502_errors_total", "Total number of 502 errors")
http_500_counter = Counter("http_500_errors_total", "Total number of 500 errors")
http_200_counter = Counter("http_200_errors_total", "Total number of 200 response")


async def get_redis_client() -> Redis:
    redis = await aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        max_connections=10,
        encoding="utf8",
        decode_responses=True,
    )
    return redis

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
