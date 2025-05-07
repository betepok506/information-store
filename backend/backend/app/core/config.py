import os
import secrets
from enum import Enum
from typing import Any

from pydantic import AnyHttpUrl, EmailStr, PostgresDsn, field_validator, HttpUrl
from pydantic_core.core_schema import FieldValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModeEnum(str, Enum):
    development = "development"
    production = "production"
    testing = "testing"


class Settings(BaseSettings):
    MODE: ModeEnum = ModeEnum.development
    API_VERSION: str = "v1"
    API_V1_STR: str = f"/api/{API_VERSION}"
    PROJECT_NAME: str

    RABBITMQ_URL: str = "amqp://admin:secret@130.100.7.137:5672/"
    
    POSTGRESQL_USERNAME: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_HOST: str
    POSTGRESQL_PORT: int
    POSTGRESQL_DATABASE: str

    DB_POOL_SIZE: int = 83
    WEB_CONCURRENCY: int = 9
    POOL_SIZE: int = max(DB_POOL_SIZE // WEB_CONCURRENCY, 5)
    ASYNC_DATABASE_URI: PostgresDsn | str = ""

    @field_validator("ASYNC_DATABASE_URI", mode="after")
    def assemble_db_connection(cls, v: str | None, info: FieldValidationInfo) -> Any:
        if isinstance(v, str):
            if v == "":
                return PostgresDsn.build(
                    scheme="postgresql+asyncpg",
                    username=info.data["POSTGRESQL_USERNAME"],
                    password=info.data["POSTGRESQL_PASSWORD"],
                    host=info.data["POSTGRESQL_HOST"],
                    port=info.data["POSTGRESQL_PORT"],
                    path=info.data["POSTGRESQL_DATABASE"],
                )
        return v

    ELASTIC_SEARCH_DATABASE_HOST: str
    ELASTIC_SEARCH_DATABASE_PORT: int
    ELASTIC_SEARCH_DATABASE_URI: HttpUrl | str = ""
    ELASTIC_VECTOR_INDEX: str = "text_vectors"
    ELASTIC_VECTOR_DIMS: int = 768

    @field_validator("ELASTIC_SEARCH_DATABASE_URI", mode="after")
    def assemble_elastic_db_connection(
        cls, v: str | None, info: FieldValidationInfo
    ) -> Any:
        if isinstance(v, str):
            if v == "":
                return str(
                    HttpUrl.build(
                        scheme="http",
                        host=info.data["ELASTIC_SEARCH_DATABASE_HOST"],
                        port=info.data["ELASTIC_SEARCH_DATABASE_PORT"],
                    )
                )
        return v

    FIRST_SUPERUSER_EMAIL: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    SECRET_KEY: str = secrets.token_urlsafe(32)
    ENCRYPT_KEY: str = secrets.token_urlsafe(32)
    BACKEND_CORS_ORIGINS: list[str] | list[AnyHttpUrl]

    @field_validator("BACKEND_CORS_ORIGINS")
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=os.path.expanduser("~/.env")
    )


settings = Settings()
