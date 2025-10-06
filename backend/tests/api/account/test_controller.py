import pytest
from httpx import AsyncClient
from models.users import Users
from unittest.mock import patch


class TestGetUserProfileAPI:
    """Test GET /api/account/profile endpoint"""

    @pytest.mark.asyncio
    async def test_get_user_profile_success(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test successful user profile retrieval with valid authentication"""
        try:
            response = await client.get(
                "/api/account/profile",
                headers={"Authorization": account_auth_headers["Authorization"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "User profile retrieved successfully"
            assert data["data"]["id"] == account_test_user.id
            assert data["data"]["email"] == account_test_user.email
            assert data["data"]["first_name"] == account_test_user.first_name
            assert data["data"]["last_name"] == account_test_user.last_name
            assert data["data"]["phone"] == account_test_user.phone
            assert data["data"]["status"] == account_test_user.status
            assert "created_at" in data["data"]
        except Exception as e:
            print(f"Test failed with exception: {str(e)}")
            raise

    @pytest.mark.asyncio
    async def test_get_user_profile_unauthorized(self, client: AsyncClient):
        """Test profile access without authentication token"""
        response = await client.get("/api/account/profile")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_profile_invalid_token(self, client: AsyncClient):
        """Test profile access with invalid authentication token"""
        response = await client.get(
            "/api/account/profile", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_profile_user_not_found(
        self, client: AsyncClient, account_auth_headers: dict
    ):
        """Test profile access when user doesn't exist in database"""
        # Mock get_user_by_id to return None
        with patch("api.account.controller.get_user_by_id", return_value=None):
            response = await client.get(
                "/api/account/profile",
                headers={"Authorization": account_auth_headers["Authorization"]},
            )

            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 404
            assert data["message"] == "User not found"

    @pytest.mark.asyncio
    async def test_get_user_profile_service_error(
        self, client: AsyncClient, account_auth_headers: dict
    ):
        """Test profile access when service layer raises an exception"""
        # Mock get_user_by_id to raise an exception
        with patch(
            "api.account.controller.get_user_by_id",
            side_effect=Exception("Database error"),
        ):
            response = await client.get(
                "/api/account/profile",
                headers={"Authorization": account_auth_headers["Authorization"]},
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_user_profile_malformed_auth_header(self, client: AsyncClient):
        """Test profile access with malformed authorization header"""
        malformed_headers = ["InvalidFormat", "Bearer", "Basic token123", "Bearer ", ""]

        for header in malformed_headers:
            response = await client.get(
                "/api/account/profile", headers={"Authorization": header}
            )
            assert response.status_code == 401


class TestUpdateUserProfileAPI:
    """Test PUT /api/account/profile endpoint"""

    @pytest.mark.asyncio
    async def test_update_user_profile_success(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test successful profile update with all fields"""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
            "phone": "+9876543210",
        }

        response = await client.put(
            "/api/account/profile",
            json=update_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "User profile updated successfully"
        assert data["data"]["first_name"] == "Updated"
        assert data["data"]["last_name"] == "Name"
        assert data["data"]["email"] == "updated@example.com"
        assert data["data"]["phone"] == "+9876543210"

    @pytest.mark.asyncio
    async def test_update_user_profile_partial(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test partial profile update with only some fields"""
        update_data = {"first_name": "PartialUpdate"}

        response = await client.put(
            "/api/account/profile",
            json=update_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["first_name"] == "PartialUpdate"
        assert data["data"]["last_name"] == account_test_user.last_name
        assert data["data"]["email"] == account_test_user.email

    @pytest.mark.asyncio
    async def test_update_user_profile_unauthorized(self, client: AsyncClient):
        """Test profile update without authentication"""
        update_data = {"first_name": "Test"}

        response = await client.put("/api/account/profile", json=update_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_user_profile_invalid_email(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test profile update with invalid email format"""
        update_data = {"email": "invalid-email-format"}

        response = await client.put(
            "/api/account/profile",
            json=update_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_user_profile_empty_fields(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test profile update with empty string fields"""
        update_data = {"first_name": "", "last_name": ""}

        response = await client.put(
            "/api/account/profile",
            json=update_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_user_profile_email_already_exists(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test profile update with email that already exists"""
        # Mock update_user_profile to raise ValueError
        with patch(
            "api.account.controller.update_user_profile",
            side_effect=ValueError("Email already exists"),
        ):
            update_data = {"email": "existing@example.com"}

            response = await client.put(
                "/api/account/profile",
                json=update_data,
                headers={"Authorization": account_auth_headers["Authorization"]},
            )

            assert response.status_code == 409
            data = response.json()
            assert data["code"] == 409
            assert data["message"] == "Email already exists"

    @pytest.mark.asyncio
    async def test_update_user_profile_user_not_found(
        self, client: AsyncClient, account_auth_headers: dict
    ):
        """Test profile update when user doesn't exist"""
        # Mock update_user_profile to return None
        with patch("api.account.controller.update_user_profile", return_value=None):
            update_data = {"first_name": "Test"}

            response = await client.put(
                "/api/account/profile",
                json=update_data,
                headers={"Authorization": account_auth_headers["Authorization"]},
            )

            print(f"Actual status code: {response.status_code}")
            print(f"Actual response: {response.json()}")

            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 404
            assert data["message"] == "User not found"

    @pytest.mark.asyncio
    async def test_update_user_profile_service_error(
        self, client: AsyncClient, account_auth_headers: dict
    ):
        """Test profile update when service layer raises an exception"""
        # Mock update_user_profile to raise an exception
        with patch(
            "api.account.controller.update_user_profile",
            side_effect=Exception("Database error"),
        ):
            update_data = {"first_name": "Test"}

            response = await client.put(
                "/api/account/profile",
                json=update_data,
                headers={"Authorization": account_auth_headers["Authorization"]},
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_update_user_profile_malformed_json(
        self, client: AsyncClient, account_auth_headers: dict
    ):
        """Test profile update with malformed JSON data"""
        response = await client.put(
            "/api/account/profile",
            data="invalid json",
            headers={
                "Authorization": account_auth_headers["Authorization"],
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_profile_with_extra_fields(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test profile update with extra fields that should be ignored"""
        update_data = {
            "first_name": "Test",
            "extra_field": "should_be_ignored",
            "another_extra": 123,
        }

        response = await client.put(
            "/api/account/profile",
            json=update_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["first_name"] == "Test"
        # Extra fields should be ignored by Pydantic


class TestChangePasswordAPI:
    """Test PUT /api/account/password endpoint"""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test successful password change with valid current password"""
        password_data = {
            "current_password": "AccountTestPassword123!",
            "new_password": "NewPassword123!",
            "logout_all_devices": False,
        }

        response = await client.put(
            "/api/account/password",
            json=password_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "Password changed successfully"
        # data field is excluded when None due to response_model_exclude_unset=True

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_password(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test password change with incorrect current password"""
        password_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword123!",
            "logout_all_devices": False,
        }

        response = await client.put(
            "/api/account/password",
            json=password_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 401
        assert data["message"] == "Current password is incorrect"

    @pytest.mark.asyncio
    async def test_change_password_unauthorized(self, client: AsyncClient):
        """Test password change without authentication"""
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewPassword123!",
            "logout_all_devices": False,
        }

        response = await client.put("/api/account/password", json=password_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test password change with weak new password"""
        password_data = {
            "current_password": "AccountTestPassword123!",
            "new_password": "123",  # Too weak
            "logout_all_devices": False,
        }

        response = await client.put(
            "/api/account/password",
            json=password_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_change_password_missing_fields(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test password change with missing required fields"""
        password_data = {
            "current_password": "AccountTestPassword123!"
        }  # Missing new_password

        response = await client.put(
            "/api/account/password",
            json=password_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_change_password_same_password(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test password change with same current and new password"""
        password_data = {
            "current_password": "AccountTestPassword123!",
            "new_password": "AccountTestPassword123!",  # Same as current
            "logout_all_devices": False,
        }

        response = await client.put(
            "/api/account/password",
            json=password_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )
        # Should succeed (business logic allows same password)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_with_logout_all_devices(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test password change with logout all devices option"""
        password_data = {
            "current_password": "AccountTestPassword123!",
            "new_password": "NewPassword123!",
            "logout_all_devices": True,
        }

        response = await client.put(
            "/api/account/password",
            json=password_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "Password changed successfully"

    @pytest.mark.asyncio
    async def test_change_password_service_error(
        self, client: AsyncClient, account_auth_headers: dict
    ):
        """Test password change when service layer raises an exception"""
        # Mock change_password to raise an exception
        with patch(
            "api.account.controller.change_password",
            side_effect=Exception("Database error"),
        ):
            password_data = {
                "current_password": "AccountTestPassword123!",
                "new_password": "NewPassword123!",
                "logout_all_devices": False,
            }

            response = await client.put(
                "/api/account/password",
                json=password_data,
                headers={"Authorization": account_auth_headers["Authorization"]},
            )

            assert response.status_code == 500
            data = response.json()
            assert data["code"] == 500
            assert data["message"] == "Database error"

    @pytest.mark.asyncio
    async def test_change_password_authentication_exception(
        self, client: AsyncClient, account_auth_headers: dict
    ):
        """Test password change when service raises AuthenticationException"""
        from utils.custom_exception import AuthenticationException

        # Mock change_password to raise AuthenticationException
        with patch(
            "api.account.controller.change_password",
            side_effect=AuthenticationException("Current password is incorrect"),
        ):
            password_data = {
                "current_password": "WrongPassword123!",
                "new_password": "NewPassword123!",
                "logout_all_devices": False,
            }

            response = await client.put(
                "/api/account/password",
                json=password_data,
                headers={"Authorization": account_auth_headers["Authorization"]},
            )

            assert response.status_code == 401
            data = response.json()
            assert data["code"] == 401
            assert data["message"] == "Current password is incorrect"


class TestControllerIntegration:
    """Test controller layer integration scenarios"""

    @pytest.mark.asyncio
    async def test_full_user_workflow(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test complete user workflow: get profile -> update profile -> change password"""
        # 1. Get initial profile
        response = await client.get(
            "/api/account/profile",
            headers={"Authorization": account_auth_headers["Authorization"]},
        )
        assert response.status_code == 200
        initial_data = response.json()["data"]

        # 2. Update profile
        update_data = {
            "first_name": "Updated",
            "last_name": "User",
            "email": "updated@example.com",
        }
        response = await client.put(
            "/api/account/profile",
            json=update_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )
        assert response.status_code == 200
        updated_data = response.json()["data"]
        assert updated_data["first_name"] == "Updated"
        assert updated_data["email"] == "updated@example.com"

        # 3. Change password
        password_data = {
            "current_password": "AccountTestPassword123!",
            "new_password": "NewPassword123!",
            "logout_all_devices": False,
        }
        response = await client.put(
            "/api/account/password",
            json=password_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )
        assert response.status_code == 200

        # 4. Verify profile still accessible after password change
        response = await client.get(
            "/api/account/profile",
            headers={"Authorization": account_auth_headers["Authorization"]},
        )
        assert response.status_code == 200
        final_data = response.json()["data"]
        assert final_data["first_name"] == "Updated"
        assert final_data["email"] == "updated@example.com"

    @pytest.mark.asyncio
    async def test_error_recovery(
        self, client: AsyncClient, account_test_user: Users, account_auth_headers: dict
    ):
        """Test error recovery scenarios"""
        # 1. Try invalid profile update
        invalid_data = {"email": "invalid-email"}
        response = await client.put(
            "/api/account/profile",
            json=invalid_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )
        assert response.status_code == 422

        # 2. Try valid profile update after error
        valid_data = {"first_name": "RecoveryTest"}
        response = await client.put(
            "/api/account/profile",
            json=valid_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )
        assert response.status_code == 200

        # 3. Try wrong password change
        wrong_password_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword123!",
            "logout_all_devices": False,
        }
        response = await client.put(
            "/api/account/password",
            json=wrong_password_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )
        assert response.status_code == 401

        # 4. Try correct password change after error
        correct_password_data = {
            "current_password": "AccountTestPassword123!",
            "new_password": "NewPassword123!",
            "logout_all_devices": False,
        }
        response = await client.put(
            "/api/account/password",
            json=correct_password_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )
        assert response.status_code == 200


class TestControllerEdgeCases:
    """Test controller layer edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_large_payload_handling(
        self, client: AsyncClient, account_auth_headers: dict
    ):
        """Test handling of large payloads"""
        # Test with very long strings
        large_data = {
            "first_name": "A" * 50,  # Max length
            "last_name": "B" * 50,  # Max length
            "phone": "1" * 20,  # Max length
        }

        response = await client.put(
            "/api/account/profile",
            json=large_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )

        # Should succeed with valid max-length data
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unicode_handling(
        self, client: AsyncClient, account_auth_headers: dict
    ):
        """Test handling of unicode characters"""
        unicode_data = {
            "first_name": "測試",
            "last_name": "用户",
            "phone": "+886-1234-5678",
        }

        response = await client.put(
            "/api/account/profile",
            json=unicode_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["first_name"] == "測試"
        assert data["data"]["last_name"] == "用户"

    @pytest.mark.asyncio
    async def test_special_characters_in_phone(
        self, client: AsyncClient, account_auth_headers: dict
    ):
        """Test handling of special characters in phone field"""
        special_phone_data = {"phone": "+1 (555) 123-4567"}  # Special characters

        response = await client.put(
            "/api/account/profile",
            json=special_phone_data,
            headers={"Authorization": account_auth_headers["Authorization"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["phone"] == "+1 (555) 123-4567"

    @pytest.mark.asyncio
    async def test_malformed_json_handling(
        self, client: AsyncClient, account_auth_headers: dict
    ):
        """Test handling of various malformed JSON scenarios"""
        malformed_cases = [
            '{"first_name": "Test", "last_name":}',  # Missing value
            '{"first_name": "Test", "last_name": "User",}',  # Trailing comma
            '{"first_name": "Test" "last_name": "User"}',  # Missing comma
            '{"first_name": "Test", "last_name": "User"',  # Missing closing brace
        ]

        for malformed_json in malformed_cases:
            response = await client.put(
                "/api/account/profile",
                data=malformed_json,
                headers={
                    "Authorization": account_auth_headers["Authorization"],
                    "Content-Type": "application/json",
                },
            )
            assert response.status_code == 422
