import uuid
import pytest
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_create_user():
    unique_email = f"testuser_{uuid.uuid4()}@example.com"
    response = client.post("/api/users/", json={
        "first_name": "Test",
        "last_name": "User",
        "email": unique_email,
        "phone": "0912345678",
        "password": "testpassword"
    })
    assert response.status_code == 201
    assert response.json()["code"] == 201

def test_get_users():
    response = client.get("/api/users/")
    assert response.status_code == 200
    assert "users" in response.json()["data"]

def test_get_user_by_id():
    unique_email = f"queryuser_{uuid.uuid4()}@example.com"
    create_resp = client.post("/api/users/", json={
        "first_name": "Query",
        "last_name": "User",
        "email": unique_email,
        "phone": "0987654321",
        "password": "testpassword"
    })
    assert create_resp.status_code == 201
    user_id = create_resp.json()["data"]["id"]
    response = client.get(f"/api/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == user_id

def test_update_user():
    unique_email = f"updateuser_{uuid.uuid4()}@example.com"
    create_resp = client.post("/api/users/", json={
        "first_name": "Update",
        "last_name": "User",
        "email": unique_email,
        "phone": "0911222333",
        "password": "testpassword"
    })
    assert create_resp.status_code == 201
    user_id = create_resp.json()["data"]["id"]
    response = client.put(f"/api/users/{user_id}", json={
        "first_name": "Updated"
    })
    assert response.status_code == 200
    assert response.json()["data"]["first_name"] == "Updated"

def test_delete_user():
    unique_email = f"deleteuser_{uuid.uuid4()}@example.com"
    create_resp = client.post("/api/users/", json={
        "first_name": "Delete",
        "last_name": "User",
        "email": unique_email,
        "phone": "0922333444",
        "password": "testpassword"
    })
    assert create_resp.status_code == 201
    user_id = create_resp.json()["data"]["id"]
    response = client.delete(f"/api/users/{user_id}")
    assert response.status_code == 200
    response = client.get(f"/api/users/{user_id}")
    assert response.status_code == 404
