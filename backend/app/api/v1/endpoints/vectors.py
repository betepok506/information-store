from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, Depends, Response
from fastapi_pagination import Params

from app.api.deps import get_elasticsearch_client
from app.core.config import settings
from app.schemas import (
    IGetResponsePaginated,
    IPostResponseBase,
    ITextVectorBaseRead,
    ITextVectorCreate,
    ITextVectorSearch,
    ITextVectorSearchRead,
    create_response,
)

router = APIRouter()


@router.post("")
async def add_vector(
    text_vector: ITextVectorCreate,
    es: AsyncElasticsearch = Depends(get_elasticsearch_client),
) -> IPostResponseBase[ITextVectorBaseRead]:
    try:
        item = await es.index(
            index=settings.ELASTIC_VECTOR_INDEX,
            body={"text": "sdsdas", "vector": text_vector.vector},
        )
        print(f"{item['_id']=}")
        return create_response(
            data=ITextVectorBaseRead(
                index=item["_index"], id=item["_id"], vector=text_vector.vector
            ),
            message="Вектор добавлен успешно",
        )
    except Exception as e:
        print()
        return Response(f"Internal server error. Error: {e}", status_code=500)


@router.post("/search_neighbors")
async def search_neighbors(
    text_vector: ITextVectorSearch,
    es: AsyncElasticsearch = Depends(get_elasticsearch_client),
) -> IGetResponsePaginated[ITextVectorSearchRead]:
    index_name = settings.ELASTIC_VECTOR_INDEX
    query = {
        "query": {
            "knn": {
                "field": "vector",
                "query_vector": text_vector.vector,
                "k": text_vector.k,
            }
        }
    }
    count_elem = await es.count(index=index_name)
    result = await es.search(index=index_name, body=query, size=text_vector.k)

    # todo: Проверить случай, когда элементов не найдено
    response = []
    for v in result["hits"]["hits"]:
        response.append(
            ITextVectorSearchRead(
                id=v["_id"],
                index=v["_index"],
                score=v["_score"],
                vector=v["_source"]["vector"],
            )
        )

    params = Params()
    params.page = 1
    params.size = count_elem["count"]
    response = IGetResponsePaginated.create(
        response, total=len(response), params=params
    )
    return create_response(data=response, message="Search Results")
