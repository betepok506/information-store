import asyncio
import gc
import os
import time
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    HTTPException,
    Request
)
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware
from prometheus_client import generate_latest
from backend.app.db.init_elastic_db import create_indexes

from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse
from backend.app.api.deps import (
    http_200_counter,
    http_404_counter,
    http_500_counter,
    http_502_counter,
    request_count,
    request_latency,
)
from backend.app.api.v1.api import api_router as api_router_v1
from backend.app.core.config import ModeEnum, settings
from backend.app.utils.fastapi_globals import GlobalsMiddleware, g
from backend.app.core.rabbitmq import RabbitMQClient
from backend.app.services.message_processing import TextDataMessageProcessor
from backend.app.consumers.handlers.message_handlers import handle_message_event


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
    # Startup
    await setup_rabbitmq()
    await create_indexes()
    yield
    # shutdown
    await rabbitmq_client.close()
    g.cleanup()
    gc.collect()


# Core Application Instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


app.add_middleware(
    SQLAlchemyMiddleware,
    db_url=str(settings.ASYNC_DATABASE_URI),
    engine_args={
        "echo": False,
        "poolclass": (
            NullPool if settings.MODE == ModeEnum.testing else AsyncAdaptedQueuePool
        ),
        # "pool_pre_ping": True,
        # "pool_size": settings.POOL_SIZE,
        # "max_overflow": 64,
    },
)
app.add_middleware(GlobalsMiddleware)

# Set all CORS origins enabled
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class CustomException(Exception):
    http_code: int
    code: str
    message: str

    def __init__(
        self,
        http_code: int = 500,
        code: str | None = None,
        message: str = "This is an error message",
    ):
        self.http_code = http_code
        self.code = code if code else str(self.http_code)
        self.message = message


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

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
