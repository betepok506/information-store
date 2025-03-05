from typing import List

from pydantic import BaseModel, field_validator

from backend.app.core.config import settings

VECTOR_LEN = settings.ELASTIC_VECTOR_DIMS


class TextVectorBase(BaseModel):
    vector: List[float]

    @field_validator(
        "vector", mode="before", json_schema_input_type=List[float]
    )
    @classmethod
    def vector_validator(csl, v):
        if len(v) != VECTOR_LEN:
            raise ValueError(f"The length of the array must be {VECTOR_LEN}!")
        return v


class ITextVectorCreate(TextVectorBase):
    pass


class ITextVectorSearch(TextVectorBase):
    k: int = 10

    @field_validator("k", mode="before", json_schema_input_type=int)
    @classmethod
    def k_validator(csl, v):
        if v <= 0:
            raise ValueError("The number of requested items must be >= 1")
        return v


class ITextVectorBaseRead(TextVectorBase):
    index: str
    id: str


class ITextVectorSearchRead(ITextVectorBaseRead, ITextVectorSearch):
    score: float
    # vector: List[float]
