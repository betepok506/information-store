# tests/test_text_data.py

import uuid
import pytest
from http import HTTPStatus
from fastapi.testclient import TestClient

from app.core.config import settings
from app.schemas import ITextDataCreateRequest, ITextDataUpdateRequest

TEXT_DATA_ENDPOINT = "/api/v1/text"


def test_create_text_data(client: TestClient, elastic_index):
    payload = {
        "text": "string",
        "url": "string",
        "source_name": "string",
        "vector": [1.0] * settings.ELASTIC_VECTOR_DIMS,
    }
    response = client.post(TEXT_DATA_ENDPOINT, json=payload)
    print("Response status code:", response.status_code)
    print("Response body:", response.json())
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()["data"]
    assert data["name"] == payload["name"]
    assert "id" in data


def test_get_all_text_data(client: TestClient):
    response = client.get(TEXT_DATA_ENDPOINT)
    assert response.status_code == HTTPStatus.OK
    data = response.json()["data"]
    assert isinstance(data["items"], list)


def test_get_by_id(client: TestClient):
    # First create one
    payload = {
        "url": "localhost:8090/v1",
        "text": "This is a test text.",
        "source_name": "elastic_123",
        "vector": [1] * settings.ELASTIC_VECTOR_DIMS,
    }

    create_response = client.post(TEXT_DATA_ENDPOINT, json=payload)
    created_id = create_response.json()["data"]["id"]

    # Now get by ID
    get_response = client.get(f"{TEXT_DATA_ENDPOINT}/{created_id}")
    assert get_response.status_code == HTTPStatus.OK
    assert get_response.json()["data"]["id"] == created_id


def test_update_text_data(client: TestClient):
    payload = {
        "url": "localhost:8090/v1",
        "text": "This is a test text.",
        "source_name": "elastic_123",
        "vector": [1] * settings.ELASTIC_VECTOR_DIMS,
    }

    create_response = client.post(TEXT_DATA_ENDPOINT, json=payload)
    created_id = create_response.json()["data"]["id"]

    update_payload = ITextDataUpdateRequest(name="Updated Name").dict()

    put_response = client.put(
        f"{TEXT_DATA_ENDPOINT}/{created_id}", json=update_payload
    )
    assert put_response.status_code == HTTPStatus.OK
    assert put_response.json()["data"]["name"] == "Updated Name"


def test_delete_text_data(client: TestClient):
    payload = {
        "url": "localhost:8090/v1",
        "text": "This is a test text.",
        "source_name": "elastic_123",
        "vector": [1] * settings.ELASTIC_VECTOR_DIMS,
    }

    create_response = client.post(TEXT_DATA_ENDPOINT, json=payload)
    created_id = create_response.json()["data"]["id"]

    delete_response = client.delete(f"{TEXT_DATA_ENDPOINT}/{created_id}")
    assert delete_response.status_code == HTTPStatus.OK

    get_response = client.get(f"{TEXT_DATA_ENDPOINT}/{created_id}")
    assert get_response.status_code == HTTPStatus.NOT_FOUND
