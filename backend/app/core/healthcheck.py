import logging

from elasticsearch import AsyncElasticsearch, ConnectionError, TransportError
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

logger = logging.getLogger(__name__)


class ServiceUnavailableError(Exception):
    pass


@retry(
    stop=stop_after_attempt(20),
    wait=wait_fixed(3),
    retry=retry_if_exception_type(ServiceUnavailableError),
    before_sleep=lambda _: logger.warning("Retrying service connection..."),
)
async def wait_for_postgres(db: AsyncSession):
    try:
        await db.exec(text("SELECT 1"))
        logger.info("PostgreSQL connection established")
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {str(e)}")
        raise ServiceUnavailableError("PostgreSQL not available")


@retry(
    stop=stop_after_attempt(20),
    wait=wait_fixed(3),
    retry=retry_if_exception_type((ConnectionError, TransportError)),
    before_sleep=lambda _: logger.warning(
        "Retrying Elasticsearch connection..."
    ),
)
async def wait_for_elasticsearch(es: AsyncElasticsearch):
    try:
        if not await es.ping():
            raise ServiceUnavailableError("Elasticsearch ping failed")
        logger.info("Elasticsearch connection established")
    except Exception as e:
        logger.error(f"Elasticsearch connection failed: {str(e)}")
        raise
