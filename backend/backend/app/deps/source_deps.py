from uuid import UUID

from fastapi import Path, Query
from typing_extensions import Annotated

from backend.app import crud
from backend.app.models.source_model import Source
from backend.app.utils.exceptions.common_exception import (
    IdNotFoundException
)


async def get_source_id(
    source_id: Annotated[UUID, Path(description="The UUID id of the source")],
) -> Source:
    source = await crud.source.get(id=source_id)
    if not source:
        raise IdNotFoundException(Source, id=source_id)
    return source
