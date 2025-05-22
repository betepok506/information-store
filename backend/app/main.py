"""
Основной модуль для приложения FastAPI.

Этот модуль инициализирует и настраивает экземпляр приложения FastAPI
вместе с его промежуточным программным обеспечением, маршрутизаторами и
фоновыми задачами.

Основные обязанности включают в себя:

- Конфигурирование приложения:
    - Загружает настройки из конфигурации (app.core.config.settings).
    - Настраивает промежуточное программное обеспечение CORS и SQLAlchemy.
    - Регистрирует глобальное промежуточное программное обеспечение FastAPI
      для отслеживания показателей с помощью Prometheus.

- Инициализация сервиса:

    - Обеспечивает подключение к необходимым сервисам (PostgreSQL и
      Elasticsearch) во время запуска.
    - Инициализирует пользователей RabbitMQ соответствующими
      обработчиками сообщений.
    - Создает необходимые индексы Elasticsearch при запуске.

- Управление сроком службы:

    - Реализует асинхронный контекстный менеджер на протяжении
      всего срока службы приложения, обеспечивая правильную инициализацию
      ресурсов и плавное завершение работы
"""

import asyncio
import gc
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware
from prometheus_client import generate_latest
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

from app.api.deps import (
    get_db,
    get_elasticsearch_client,
    http_200_counter,
    http_404_counter,
    http_500_counter,
    http_502_counter,
    request_count,
    request_latency,
)
from app.api.v1.api import api_router as api_router_v1
from app.consumers.handlers.message_handlers import (
    handle_message_event,
)
from app.core.config import ModeEnum, settings
from app.core.healthcheck import (
    wait_for_elasticsearch,
    wait_for_postgres,
)
from app.core.rabbitmq import RabbitMQClient
from app.db.init_elastic_db import create_indexes
from app.services import TextDataMessageProcessor
from app.utils.fastapi_globals import GlobalsMiddleware, g
from app.utils.exceptions import add_exception_handlers

# TODO: Вывести в конфиг названия очередей
os.environ["HTTP_PROXY"] = "http://130.100.7.222:1082"
os.environ["HTTPS_PROXY"] = "http://130.100.7.222:1082"

rabbitmq_client = RabbitMQClient()


async def setup_rabbitmq():
    # Инициализация обработчиков
    processor = TextDataMessageProcessor()
    rabbitmq_client.register_handler(
        "messages", lambda msg: handle_message_event(msg, processor)
    )

    await rabbitmq_client.connect()
    asyncio.create_task(rabbitmq_client.start_consumers())


@asynccontextmanager
async def lifespan(app: FastAPI):
    es = await get_elasticsearch_client()
    db = get_db()
    # Ожидание доступности сервисов
    async with db as session:
        await wait_for_postgres(session)
    await wait_for_elasticsearch(es)

    # Startup
    await setup_rabbitmq()
    await create_indexes(es)
    yield
    # shutdown
    await rabbitmq_client.close()
    await es.close()
    g.cleanup()
    gc.collect()


# Core Application Instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    debug=True,
)


app.add_middleware(
    SQLAlchemyMiddleware,
    db_url=str(settings.ASYNC_DATABASE_URI),
    engine_args={
        "echo": False,
        "poolclass": (
            NullPool
            if settings.MODE == ModeEnum.testing
            else AsyncAdaptedQueuePool
        ),
        # "pool_pre_ping": True,
        # "pool_size": settings.POOL_SIZE,
        # "max_overflow": 64,
    },
)
app.add_middleware(GlobalsMiddleware)

# Set custom exception
add_exception_handlers(app)

# Set all CORS origins enabled
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin) for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# class CustomException(Exception):
#     http_code: int
#     code: str
#     message: str

#     def __init__(
#         self,
#         http_code: int = 500,
#         code: str | None = None,
#         message: str = "This is an error message",
#     ):
#         self.http_code = http_code
#         self.code = code if code else str(self.http_code)
#         self.message = message


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    request_count.inc()
    try:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        request_latency.observe(process_time)
        http_200_counter.inc()
    except Exception as e:
        if isinstance(e, HTTPException) and e.status_code == 404:
            http_404_counter.inc()
        elif isinstance(e, HTTPException) and e.status_code == 502:
            http_502_counter.inc()
        elif isinstance(e, HTTPException) and e.status_code == 500:
            http_500_counter.inc()
        raise e
    else:
        if response.status_code == 404:
            http_404_counter.inc()
        elif response.status_code == 502:
            http_502_counter.inc()
        elif response.status_code == 500:
            http_500_counter.inc()
    return response


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return generate_latest()


@app.get("/")
async def root():
    """
    An example "Hello world" FastAPI route.
    """
    # if oso.is_allowed(user, "read", message):
    return {"message": "Hello World"}


# Add Routers
app.include_router(api_router_v1, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
