import pytest
from fastapi.testclient import TestClient

from src.wsgi import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_users(client):
    response = client.get("/api/user")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_create_user(client):
    response = client.post("/api/user/create", json={"name": "Alice"})
    assert response.status_code == 201
