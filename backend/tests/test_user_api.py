import uuid
import pytest

@pytest.mark.asyncio
async def test_create_user(client):
    unique_email = f"testuser_{uuid.uuid4()}@example.com"
    response = await client.post("/api/users/", json={
        "first_name": "Test",
        "last_name": "User",
        "email": unique_email,
        "phone": "0912345678",
        "password": "testpassword"
    })
    assert response.status_code == 201
    assert response.json()["code"] == 201

@pytest.mark.asyncio
async def test_create_user_conflict(client):
    unique_email = f"conflict_{uuid.uuid4()}@example.com"
    user_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": unique_email,
        "phone": "0912345678",
        "password": "testpassword"
    }
    # First creation
    resp1 = await client.post("/api/users/", json=user_data)
    assert resp1.status_code == 201
    # Second creation with the same email
    resp2 = await client.post("/api/users/", json=user_data)
    assert resp2.status_code == 409
    assert resp2.json()["code"] == 409

@pytest.mark.asyncio
async def test_create_user_validation_error(client):
    response = await client.post("/api/users/", json={
        "first_name": "Test",
        "last_name": "User",
        "email": "invalid@example.com",
        "phone": "0912345678",
        "password": "123"
    })
    assert response.status_code == 422
    assert response.json()["code"] == 422
    assert "password" in str(response.json()["data"])

@pytest.mark.asyncio
async def test_get_users(client):
    unique_email = f"listuser_{uuid.uuid4()}@example.com"
    await client.post("/api/users/", json={
        "first_name": "List",
        "last_name": "User",
        "email": unique_email,
        "phone": "0912345678",
        "password": "testpassword"
    })
    response = await client.get("/api/users/")
    assert response.status_code == 200
    assert "users" in response.json()["data"]
    assert len(response.json()["data"]["users"]) > 0

@pytest.mark.asyncio
async def test_get_users_not_found(client):
    # Delete all users first or use a fresh test database
    response = await client.get("/api/users/")
    # Assume the database is empty
    assert response.status_code == 404
    assert response.json()["code"] == 404
    assert response.json()["message"] == "No users found"

@pytest.mark.asyncio
async def test_get_user_by_id(client):
    unique_email = f"queryuser_{uuid.uuid4()}@example.com"
    create_resp = await client.post("/api/users/", json={
        "first_name": "Query",
        "last_name": "User",
        "email": unique_email,
        "phone": "0987654321",
        "password": "testpassword"
    })
    assert create_resp.status_code == 201
    user_id = create_resp.json()["data"]["id"]
    
    response = await client.get(f"/api/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == user_id

@pytest.mark.asyncio
async def test_get_user_by_id_not_found(client):
    response = await client.get("/api/users/nonexistent_id")
    assert response.status_code == 404
    assert response.json()["code"] == 404
    assert response.json()["message"] == "User not found"

@pytest.mark.asyncio
async def test_update_user(client):
    unique_email = f"updateuser_{uuid.uuid4()}@example.com"
    create_resp = await client.post("/api/users/", json={
        "first_name": "Update",
        "last_name": "User",
        "email": unique_email,
        "phone": "0911222333",
        "password": "testpassword"
    })
    assert create_resp.status_code == 201
    user_id = create_resp.json()["data"]["id"]

    response = await client.put(f"/api/users/{user_id}", json={
        "first_name": "Updated"
    })
    assert response.status_code == 200
    assert response.json()["data"]["first_name"] == "Updated"

@pytest.mark.asyncio
async def test_update_user_not_found(client):
    response = await client.put("/api/users/nonexistent_id", json={"first_name": "X"})
    assert response.status_code == 404
    assert response.json()["code"] == 404
    assert response.json()["message"] == "User not found"

@pytest.mark.asyncio
async def test_update_user_email_conflict(client):
    # Create two users
    email1 = f"u1_{uuid.uuid4()}@example.com"
    email2 = f"u2_{uuid.uuid4()}@example.com"
    resp1 = await client.post("/api/users/", json={
        "first_name": "A", "last_name": "A", "email": email1, "phone": "0911", "password": "pw123456"
    })
    assert resp1.status_code == 201, f"resp1 failed: {resp1.json()}"
    resp2 = await client.post("/api/users/", json={
        "first_name": "B", "last_name": "B", "email": email2, "phone": "0922", "password": "pw654321"
    })
    assert resp2.status_code == 201, f"resp2 failed: {resp2.json()}"
    id1 = resp1.json()["data"]["id"]
    # Try to update user1's email to user2's email
    resp_conflict = await client.put(f"/api/users/{id1}", json={"email": email2})
    assert resp_conflict.status_code == 409
    assert resp_conflict.json()["code"] == 409

@pytest.mark.asyncio
async def test_delete_user(client):
    unique_email = f"deleteuser_{uuid.uuid4()}@example.com"
    create_resp = await client.post("/api/users/", json={
        "first_name": "Delete",
        "last_name": "User",
        "email": unique_email,
        "phone": "0922333444",
        "password": "testpassword"
    })
    assert create_resp.status_code == 201
    user_id = create_resp.json()["data"]["id"]

    response = await client.delete(f"/api/users/{user_id}")
    assert response.status_code == 204
    assert response.text == ""

    response = await client.get(f"/api/users/{user_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_user_not_found(client):
    response = await client.delete("/api/users/nonexistent_id")
    assert response.status_code == 404
    assert response.json()["code"] == 404
    assert response.json()["message"] == "User not found"