import gc
# import logging
import os
from contextlib import asynccontextmanager
from typing import Any
# from uuid import UUID, uuid4
import time

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware, db
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter
# from fastapi_limiter.depends import WebSocketRateLimiter
from jwt import DecodeError, ExpiredSignatureError, MissingRequiredClaimError

# from langchain.chat_models import ChatOpenAI
# from langchain.schema import HumanMessage
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from starlette.middleware.cors import CORSMiddleware

# from backend.app import crud
from backend.app.api.deps import get_redis_client
from backend.app.api.v1.api import api_router as api_router_v1
from backend.app.core.config import ModeEnum, settings
from backend.app.core.security import decode_token

from starlette.responses import PlainTextResponse
from prometheus_client import generate_latest

# from backend.app.schemas.common_schema import IChatResponse, IUserMessage
from backend.app.utils.fastapi_globals import GlobalsMiddleware, g
from backend.app.utils.uuid6 import uuid7
from backend.app.api.deps import (
    request_count, request_latency, 
    http_404_counter, http_502_counter, http_500_counter, http_200_counter)

# from transformers import pipeline


os.environ["HTTP_PROXY"] = "http://130.100.7.222:1082"
os.environ["HTTPS_PROXY"] = "http://130.100.7.222:1082"

# from pydantic import BaseModel


# class MokeModel(BaseModel):
#     id: int
#     name: str

#     def __init__(self, *args, **kwds):
#         pass

#     def __call__(self, *args, **kwds):
#         return "World!"

#     class Config:
#         orm_mode = True


async def user_id_identifier(request: Request):
    if request.scope["type"] == "http":
        # Retrieve the Authorization header from the request
        auth_header = request.headers.get("Authorization")

        if auth_header is not None:
            # Check that the header is in the correct format
            header_parts = auth_header.split()
            if len(header_parts) == 2 and header_parts[0].lower() == "bearer":
                token = header_parts[1]
                try:
                    payload = decode_token(token)
                except ExpiredSignatureError:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Your token has expired. Please log in again.",
                    )
                except DecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Error when decoding the token. Please check your request.",
                    )
                except MissingRequiredClaimError:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="There is no required field in your token. Please contact the administrator.",
                    )

                user_id = payload["sub"]

                return user_id

    if request.scope["type"] == "websocket":
        return request.scope["path"]

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]

    client = request.client
    ip = getattr(client, "host", "0.0.0.0")
    return ip + ":" + request.scope["path"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis_client = await get_redis_client()
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    await FastAPILimiter.init(redis_client, identifier=user_id_identifier)

    # Load a pre-trained sentiment analysis model as a dictionary to an easy cleanup
    # models: dict[str, Any] = {
    #     # "sentiment_model": pipeline(
    #     #     "sentiment-analysis",
    #     #     model="distilbert-base-uncased-finetuned-sst-2-english",
    #     # ),
    #     "sentiment_model": MokeModel
    # }
    # g.set_default("sentiment_model", models["sentiment_model"])
    # print("startup fastapi")
    yield
    # shutdown
    await FastAPICache.clear()
    await FastAPILimiter.close()
    # models.clear()
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
