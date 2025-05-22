# tests/conftest.py

import asyncio
import os
from typing import AsyncGenerator, Generator
from contextlib import asynccontextmanager
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
import uuid
from app.core.config import settings
from app.main import app
from app.db.session import SessionLocal


# Устанавливаем переменные окружения для тестовой БД
os.environ["TEST_DATABASE_NAME"] = "test_db"
os.environ["TEST_DATABASE_USER"] = os.getenv("POSTGRESQL_USERNAME")
os.environ["TEST_DATABASE_PASSWORD"] = os.getenv("POSTGRESQL_PASSWORD")
os.environ["TEST_DATABASE_HOST"] = os.getenv("POSTGRESQL_HOST")
os.environ["TEST_DATABASE_PORT"] = os.getenv("POSTGRESQL_PORT")
os.environ["TEST_ELASTIC_VECTOR_INDEX"] = "test_index"
os.environ["TEST_ELASTIC_SEARCH_DATABASE_URI"] = (
    settings.ELASTIC_SEARCH_DATABASE_URI
)

# Создаем движок и async сессию
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{os.environ['TEST_DATABASE_USER']}:{os.environ['TEST_DATABASE_PASSWORD']}"
    f"@{os.environ['TEST_DATABASE_HOST']}:{os.environ['TEST_DATABASE_PORT']}/ \
    {os.environ['TEST_DATABASE_NAME']}"
)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, isolation_level="AUTOCOMMIT"
)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
#     async with async_session_maker() as session:
#         yield session


@pytest.fixture
def override_get_db(db_session):
    # @asynccontextmanager
    async def _override_get_db():
        return db_session

    return _override_get_db


from app.api.deps import get_db, get_elasticsearch_client
from elasticsearch import AsyncElasticsearch


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
    async with engine.connect() as conn:
        await conn.execute(text("COMMIT"))
        await conn.execute(text("DROP DATABASE IF EXISTS test_db"))
        await conn.execute(text("CREATE DATABASE test_db"))
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def db_migrations(db_engine):
    # # Теперь подключаемся к новой БД
    # engine_new = create_async_engine(SQLALCHEMY_DATABASE_URL)

    # async with engine_new.begin() as conn:
    #     await conn.run_sync(SQLModel.metadata)

    # yield

    # await engine_new.dispose()

    """Применяет миграции к тестовой БД"""
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
    command.upgrade(alembic_cfg, "head")

    yield


@pytest.fixture(scope="function")
async def db_session(db_engine, db_migrations) -> AsyncSession:
    """Возвращает реальный AsyncSession для использования в тестах и Depends(get_db)"""
    connection = await db_engine.connect()
    transaction = await connection.begin()

    session = AsyncSession(bind=connection)

    yield session

    await session.rollback()
    await connection.rollback()
    await session.close()
    await connection.close()


@pytest.fixture
def client(override_get_db, es_client) -> Generator[TestClient, None, None]:
    async def _get_elasticsearch_override():
        yield es_client

    # @asynccontextmanager
    # async def _override_get_db():
    #     async with db_session as session:
    #         yield session

    # Переопределяем зависимости
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_elasticsearch_client] = (
        _get_elasticsearch_override
    )
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def elastic_index_name():
    return os.environ["TEST_ELASTIC_VECTOR_INDEX"]


@pytest.fixture(scope="function")
def override_get_elasticsearch(es_client, elastic_index):
    async def _override_get_elasticsearch():
        yield es_client

    return _override_get_elasticsearch


@pytest.fixture(scope="session")
async def es_client():
    client = AsyncElasticsearch(
        hosts=[os.environ["TEST_ELASTIC_SEARCH_DATABASE_URI"]]
    )

    async def delete_indices():
        if await client.indices.exists(index="test_*"):
            await client.indices.delete(index="test_*")

    await delete_indices()

    yield client

    await delete_indices()
    await client.close()


@pytest.fixture(scope="function")
async def elastic_index(es_client, elastic_index_name):
    index_name = f"{elastic_index_name}_{uuid.uuid4().hex}"

    # Создаём новый индекс
    await es_client.indices.create(index=index_name)

    yield index_name

    # Удаляем индекс после теста
    if await es_client.indices.exists(index=index_name):
        await es_client.indices.delete(index=index_name)
