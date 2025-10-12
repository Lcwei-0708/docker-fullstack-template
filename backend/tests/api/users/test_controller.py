import pytest
from datetime import datetime
from httpx import AsyncClient
from unittest.mock import patch
from api.users.schema import UserResponse, UserPagination


class TestUsersController:
    """Test Users controller API endpoints"""

    @pytest.mark.asyncio
    async def test_get_users_success(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test successful users retrieval with valid authentication"""
        with patch("api.users.controller.get_all_users") as mock_get_users:
            mock_pagination = UserPagination(
                users=[
                    UserResponse(
                        id="user1",
                        email="user1@example.com",
                        first_name="User",
                        last_name="One",
                        phone="+1234567890",
                        status=True,
                        created_at=datetime.now(),
                        role="admin",
                    )
                ],
                total=1,
                page=1,
                per_page=10,
                total_pages=1,
            )
            mock_get_users.return_value = mock_pagination

            response = await client.get(
                "/api/users/",
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "Successfully retrieved users"
            assert "data" in data
            assert "users" in data["data"]
            assert len(data["data"]["users"]) == 1

    @pytest.mark.asyncio
    async def test_get_users_unauthorized(self, client: AsyncClient):
        """Test users access without authentication token"""
        response = await client.get("/api/users/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_users_with_filters(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test users retrieval with search filters"""
        with patch("api.users.controller.get_all_users") as mock_get_users:
            mock_pagination = UserPagination(
                users=[], total=0, page=1, per_page=10, total_pages=0
            )
            mock_get_users.return_value = mock_pagination

            response = await client.get(
                "/api/users/?keyword=test&status=true&role=admin&page=1&per_page=5&sort_by=email&desc=true",
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            mock_get_users.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_success(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test successful user creation"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "password": "TestPassword123!",
            "status": True,
            "role": "admin",
        }

        with patch("api.users.controller.create_user") as mock_create_user:
            mock_user = UserResponse(
                id="new-user-id",
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                phone=user_data["phone"],
                status=user_data["status"],
                created_at=datetime.now(),
                role=user_data["role"],
            )
            mock_create_user.return_value = mock_user

            response = await client.post(
                "/api/users/",
                json=user_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "User created successfully"
            assert data["data"]["email"] == user_data["email"]

    @pytest.mark.asyncio
    async def test_create_user_email_exists(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test user creation with existing email"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "existing@example.com",
            "phone": "+1234567890",
            "password": "TestPassword123!",
            "status": True,
        }

        with patch("api.users.controller.create_user") as mock_create_user:
            mock_create_user.side_effect = Exception("Email already exists")

            response = await client.post(
                "/api/users/",
                json=user_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 409
            data = response.json()
            assert data["code"] == 409
            assert data["message"] == "Email already exists"

    @pytest.mark.asyncio
    async def test_create_user_server_error(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test user creation with server error"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "password": "TestPassword123!",
            "status": True,
        }

        with patch("api.users.controller.create_user") as mock_create_user:
            mock_create_user.side_effect = Exception("Database error")

            response = await client.post(
                "/api/users/",
                json=user_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_update_user_success(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test successful user update"""
        user_id = "test-user-id"
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
        }

        with patch("api.users.controller.update_user") as mock_update_user:
            mock_user = UserResponse(
                id=user_id,
                email=update_data["email"],
                first_name=update_data["first_name"],
                last_name=update_data["last_name"],
                phone="+1234567890",
                status=True,
                created_at=datetime.now(),
                role="admin",
            )
            mock_update_user.return_value = mock_user

            response = await client.put(
                f"/api/users/{user_id}",
                json=update_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "User updated successfully"
            assert data["data"]["first_name"] == update_data["first_name"]

    @pytest.mark.asyncio
    async def test_update_user_not_found(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test user update with non-existent user"""
        user_id = "nonexistent-user-id"
        update_data = {"first_name": "Updated"}

        with patch("api.users.controller.update_user") as mock_update_user:
            mock_update_user.side_effect = Exception("User not found")

            response = await client.put(
                f"/api/users/{user_id}",
                json=update_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 404
            assert data["message"] == "User not found"

    @pytest.mark.asyncio
    async def test_delete_users_success(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test successful users deletion"""
        delete_data = {"user_ids": ["user1", "user2", "user3"]}

        with patch("api.users.controller.delete_users") as mock_delete_users:
            mock_delete_users.return_value = True

            response = await client.request(
                "DELETE",
                "/api/users/",
                json=delete_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "Users deleted successfully"
            assert data["data"]["deleted_count"] == 3

    @pytest.mark.asyncio
    async def test_delete_users_not_found(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test users deletion with non-existent users"""
        delete_data = {"user_ids": ["nonexistent1", "nonexistent2"]}

        with patch("api.users.controller.delete_users") as mock_delete_users:
            mock_delete_users.side_effect = Exception(
                "Users not found: nonexistent1, nonexistent2"
            )

            response = await client.request(
                "DELETE",
                "/api/users/",
                json=delete_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 404

    @pytest.mark.asyncio
    async def test_reset_password_success(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test successful password reset"""
        user_id = "test-user-id"
        password_data = {"new_password": "NewPassword123!"}

        with patch("api.users.controller.reset_user_password") as mock_reset_password:
            mock_reset_password.return_value = True

            response = await client.post(
                f"/api/users/{user_id}/reset-password",
                json=password_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert (
                data["message"]
                == "Password reset successfully and all devices logged out"
            )

    @pytest.mark.asyncio
    async def test_reset_password_user_not_found(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test password reset with non-existent user"""
        user_id = "nonexistent-user-id"
        password_data = {"new_password": "NewPassword123!"}

        with patch("api.users.controller.reset_user_password") as mock_reset_password:
            mock_reset_password.side_effect = Exception("User not found")

            response = await client.post(
                f"/api/users/{user_id}/reset-password",
                json=password_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 404
            assert data["message"] == "User not found"

    @pytest.mark.asyncio
    async def test_reset_password_server_error(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test password reset with server error"""
        user_id = "test-user-id"
        password_data = {"new_password": "NewPassword123!"}

        with patch("api.users.controller.reset_user_password") as mock_reset_password:
            mock_reset_password.side_effect = Exception("Database error")

            response = await client.post(
                f"/api/users/{user_id}/reset-password",
                json=password_data,
                headers={"Authorization": users_auth_headers["Authorization"]},
            )

            assert response.status_code == 500


class TestUsersControllerValidation:
    """Test Users controller input validation"""

    @pytest.mark.asyncio
    async def test_create_user_invalid_email(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test user creation with invalid email format"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email",
            "phone": "+1234567890",
            "password": "TestPassword123!",
            "status": True,
        }

        response = await client.post(
            "/api/users/",
            json=user_data,
            headers={"Authorization": users_auth_headers["Authorization"]},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_user_short_password(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test user creation with password too short"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "password": "123",
            "status": True,
        }

        response = await client.post(
            "/api/users/",
            json=user_data,
            headers={"Authorization": users_auth_headers["Authorization"]},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_users_invalid_pagination(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test users retrieval with invalid pagination parameters"""
        response = await client.get(
            "/api/users/?page=0&per_page=101",
            headers={"Authorization": users_auth_headers["Authorization"]},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_delete_users_empty_list(
        self, client: AsyncClient, users_auth_headers: dict
    ):
        """Test users deletion with empty user list"""
        delete_data = {"user_ids": []}

        response = await client.request(
            "DELETE",
            "/api/users/",
            json=delete_data,
            headers={"Authorization": users_auth_headers["Authorization"]},
        )

        assert response.status_code == 422