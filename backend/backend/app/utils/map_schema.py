from typing import TypeVar, Dict

from pydantic import BaseModel
from sqlmodel import SQLModel

SchemaType = TypeVar("SchemaType", bound=BaseModel)
ModelType = TypeVar("ModelType", bound=SQLModel)


def map_models_schema(schema: SchemaType, models: list[ModelType]):
    return [schema.model_validate(model) for model in models]


def merge_schemas(target_schema: BaseModel, update_schema: BaseModel, default_values: Dict):
    merged_dict = {}
    for field_name, field_value in target_schema.__dict__.items():
        if field_name in update_schema.__dict__:
            merged_dict[field_name] = update_schema.__dict__[field_name]
        else:
            merged_dict[field_name] = field_value

    for field_name, field_value in default_values.items():
        if field_name not in target_schema.__dict__:
            raise ValueError(f"Поле '{field_name}' отсутствует в первой схеме")
        merged_dict[field_name] = default_values[field_name]

    merged_schema = target_schema.__class__(**merged_dict)
    return merged_schema
