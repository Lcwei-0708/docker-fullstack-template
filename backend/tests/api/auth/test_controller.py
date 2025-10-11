import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from fastapi import HTTPException
from api.auth.schema import (
    UserRegister,
    UserLogin,
    ResetPasswordRequest,
    LogoutRequest,
    PasswordResetRequiredResponse,
)
from utils.custom_exception import (
    ConflictException,
    AuthenticationException,
    PasswordResetRequiredException,
    NotFoundException,
)
from core.security import (
    create_password_reset_token,
    verify_password_reset_token,
    get_token,
    verify_token,
)
from main import app


class TestAuthController:
    """Test Auth controller API endpoints"""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration"""
        register_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "password": "TestPassword123!",
        }

        with patch("api.auth.controller.register") as mock_register:
            mock_register.return_value = {
                "user": type(
                    "User",
                    (),
                    {
                        "id": "test-user-id",
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "phone": "+1234567890",
                    },
                )(),
                "session_id": "test-session-id",
                "access_token": "test-access-token",
            }

            response = await client.post("/api/auth/register", json=register_data)

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "User registered successfully"
            assert "session_id" in response.cookies

    @pytest.mark.asyncio
    async def test_register_email_already_exists(self, client: AsyncClient):
        """Test registration with existing email"""
        register_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "existing@example.com",
            "phone": "+1234567890",
            "password": "TestPassword123!",
        }

        with patch("api.auth.controller.register") as mock_register:
            mock_register.side_effect = ConflictException("Email already exists")

            response = await client.post("/api/auth/register", json=register_data)

            assert response.status_code == 409
            data = response.json()
            assert data["code"] == 409
            assert data["message"] == "Email already exists"

    @pytest.mark.asyncio
    async def test_register_server_error(self, client: AsyncClient):
        """Test registration with server error"""
        register_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "password": "TestPassword123!",
        }

        with patch("api.auth.controller.register") as mock_register:
            mock_register.side_effect = Exception("Database error")

            response = await client.post("/api/auth/register", json=register_data)

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful user login"""
        login_data = {"email": "john.doe@example.com", "password": "TestPassword123!"}

        with patch("api.auth.controller.login") as mock_login:
            mock_login.return_value = {
                "user": type(
                    "User",
                    (),
                    {
                        "id": "test-user-id",
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "phone": "+1234567890",
                    },
                )(),
                "session_id": "test-session-id",
                "access_token": "test-access-token",
            }

            response = await client.post("/api/auth/login", json=login_data)

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "User logged in successfully"
            assert "session_id" in response.cookies

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials"""
        login_data = {"email": "john.doe@example.com", "password": "WrongPassword"}

        with patch("api.auth.controller.login") as mock_login:
            mock_login.side_effect = AuthenticationException(
                "Invalid email or password"
            )

            response = await client.post("/api/auth/login", json=login_data)

            assert response.status_code == 401
            data = response.json()
            assert data["code"] == 401
            assert data["message"] == "Invalid email or password"

    @pytest.mark.asyncio
    async def test_login_server_error(self, client: AsyncClient):
        """Test login with server error"""
        login_data = {"email": "john.doe@example.com", "password": "TestPassword123!"}

        with patch("api.auth.controller.login") as mock_login:
            mock_login.side_effect = Exception("Database error")

            response = await client.post("/api/auth/login", json=login_data)

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient):
        """Test successful logout"""
        logout_data = {"logout_all": False}

        async def mock_verify_token():
            return {"sub": "test-user-id", "sid": "test-session-id"}

        with patch("api.auth.controller.logout") as mock_logout:
            mock_logout.return_value = True
            app.dependency_overrides[verify_token] = mock_verify_token

            try:
                response = await client.post("/api/auth/logout", json=logout_data)
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["message"] == "User logged out successfully"
            finally:
                app.dependency_overrides.pop(verify_token, None)

    @pytest.mark.asyncio
    async def test_logout_all_devices(self, client: AsyncClient):
        """Test logout from all devices"""
        logout_data = {"logout_all": True}

        async def mock_verify_token():
            return {"sub": "test-user-id", "sid": "test-session-id"}

        with patch("api.auth.controller.logout_all_devices") as mock_logout_all:
            mock_logout_all.return_value = True
            app.dependency_overrides[verify_token] = mock_verify_token

            try:
                response = await client.post("/api/auth/logout", json=logout_data)
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["message"] == "User logged out successfully"
            finally:
                app.dependency_overrides.pop(verify_token, None)

    @pytest.mark.asyncio
    async def test_logout_invalid_session(self, client: AsyncClient):
        """Test logout with invalid session"""
        logout_data = {"logout_all": False}

        async def mock_verify_token():
            return {"sub": "test-user-id", "sid": None}

        with patch("api.auth.controller.logout") as mock_logout:
            mock_logout.side_effect = AuthenticationException(
                "Invalid or expired session"
            )
            app.dependency_overrides[verify_token] = mock_verify_token

            try:
                response = await client.post("/api/auth/logout", json=logout_data)
                assert response.status_code == 401
                data = response.json()
                assert data["code"] == 401
                assert data["message"] == "Invalid or expired session"
            finally:
                app.dependency_overrides.pop(verify_token, None)

    @pytest.mark.asyncio
    async def test_logout_server_error(self, client: AsyncClient):
        """Test logout with server error"""
        logout_data = {"logout_all": False}

        async def mock_verify_token():
            return {"sub": "test-user-id", "sid": "test-session-id"}

        with patch("api.auth.controller.logout") as mock_logout:
            mock_logout.side_effect = Exception("Database error")
            app.dependency_overrides[verify_token] = mock_verify_token

            try:
                response = await client.post("/api/auth/logout", json=logout_data)
                assert response.status_code == 500
            finally:
                app.dependency_overrides.pop(verify_token, None)

    @pytest.mark.asyncio
    async def test_token_refresh_success(self, client: AsyncClient):
        """Test successful token refresh"""
        with patch("api.auth.controller.token") as mock_token:
            mock_token.return_value = "new-access-token"

            response = await client.post(
                "/api/auth/token", cookies={"session_id": "test-session-id"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "Token refreshed successfully"
            assert data["data"]["access_token"] == "new-access-token"

    @pytest.mark.asyncio
    async def test_token_refresh_no_session(self, client: AsyncClient):
        """Test token refresh without session cookie"""
        response = await client.post("/api/auth/token")

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 401
        assert data["message"] == "Invalid or expired session"

    @pytest.mark.asyncio
    async def test_token_refresh_invalid_session(self, client: AsyncClient):
        """Test token refresh with invalid session"""
        with patch("api.auth.controller.token") as mock_token:
            mock_token.side_effect = AuthenticationException(
                "Invalid or expired session"
            )

            response = await client.post(
                "/api/auth/token", cookies={"session_id": "invalid-session-id"}
            )

            assert response.status_code == 401
            data = response.json()
            assert data["code"] == 401
            assert data["message"] == "Invalid or expired session"

    @pytest.mark.asyncio
    async def test_token_refresh_user_not_found(self, client: AsyncClient):
        """Test token refresh with user not found"""
        with patch("api.auth.controller.token") as mock_token:
            mock_token.side_effect = NotFoundException("User not found")

            response = await client.post(
                "/api/auth/token", cookies={"session_id": "test-session-id"}
            )

            assert response.status_code == 401
            data = response.json()
            assert data["code"] == 401
            assert data["message"] == "Invalid or expired session"

    @pytest.mark.asyncio
    async def test_token_refresh_server_error(self, client: AsyncClient):
        """Test token refresh with server error"""
        with patch("api.auth.controller.token") as mock_token:
            mock_token.side_effect = Exception("Database error")

            response = await client.post(
                "/api/auth/token", cookies={"session_id": "test-session-id"}
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_login_password_reset_required(self, client: AsyncClient):
        """Test login with password reset required"""
        login_data = {"email": "reset@example.com", "password": "TestPassword123!"}

        with patch("api.auth.controller.login") as mock_login:
            details = PasswordResetRequiredResponse(
                reset_token="test-reset-token", expires_at="2024-01-01T00:00:00Z"
            )
            mock_exception = PasswordResetRequiredException("Password reset required")
            mock_exception.details = details
            mock_login.side_effect = mock_exception

            response = await client.post("/api/auth/login", json=login_data)
            assert response.status_code == 202
            data = response.json()
            assert data["code"] == 202
            assert data["message"] == "Password reset required"
            assert "reset_token" in data["data"]
            assert data["data"]["reset_token"] == "test-reset-token"

    @pytest.mark.asyncio
    async def test_reset_password_success(self, client: AsyncClient):
        """Test successful password reset"""
        reset_data = {"new_password": "NewPassword123!"}

        async def mock_verify_password_reset_token():
            return {
                "sub": "test-user-id",
                "token": "test-token",
                "email": "test@example.com",
            }

        with patch("api.auth.controller.reset_password") as mock_reset:
            mock_reset.return_value = {
                "user": type(
                    "User",
                    (),
                    {
                        "id": "test-user-id",
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "phone": "+1234567890",
                    },
                )(),
                "session_id": "test-session-id",
                "access_token": "test-access-token",
            }

            app.dependency_overrides[verify_password_reset_token] = (
                mock_verify_password_reset_token
            )

            try:
                response = await client.post(
                    "/api/auth/reset-password",
                    json=reset_data,
                    headers={"Authorization": "Bearer valid-reset-token"},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["message"] == "Password reset successfully"
            finally:
                app.dependency_overrides.pop(verify_password_reset_token, None)

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, client: AsyncClient):
        """Test password reset with invalid token"""
        reset_data = {"new_password": "NewPassword123!"}

        response = await client.post("/api/auth/reset-password", json=reset_data)

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 401
        assert data["message"] == "Invalid or expired token"

    @pytest.mark.asyncio
    async def test_reset_password_user_not_found(self, client: AsyncClient):
        """Test password reset with user not found"""
        reset_data = {"new_password": "NewPassword123!"}

        async def mock_verify_password_reset_token():
            return {
                "sub": "test-user-id",
                "token": "test-token",
                "email": "test@example.com",
            }

        with patch("api.auth.controller.reset_password") as mock_reset:
            mock_reset.side_effect = NotFoundException("User not found")
            app.dependency_overrides[verify_password_reset_token] = (
                mock_verify_password_reset_token
            )

            try:
                response = await client.post(
                    "/api/auth/reset-password",
                    json=reset_data,
                    headers={"Authorization": "Bearer valid-reset-token"},
                )
                assert response.status_code == 404
                data = response.json()
                assert data["code"] == 404
                assert data["message"] == "User not found"
            finally:
                app.dependency_overrides.pop(verify_password_reset_token, None)

    @pytest.mark.asyncio
    async def test_validate_reset_token_success(self, client: AsyncClient):
        """Test successful password reset token validation"""

        async def mock_verify_password_reset_token():
            return {
                "sub": "test-user-id",
                "token": "test-token",
                "email": "test@example.com",
            }

        with patch(
            "api.auth.controller.validate_password_reset_token"
        ) as mock_validate:
            mock_validate.return_value = type(
                "ValidationResult", (), {"is_valid": True}
            )()
            app.dependency_overrides[verify_password_reset_token] = (
                mock_verify_password_reset_token
            )

            try:
                response = await client.get(
                    "/api/auth/validate-reset-token",
                    headers={"Authorization": "Bearer valid-reset-token"},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["message"] == "Token is valid"
                assert data["data"]["is_valid"] is True
            finally:
                app.dependency_overrides.pop(verify_password_reset_token, None)

    @pytest.mark.asyncio
    async def test_validate_reset_token_invalid(self, client: AsyncClient):
        """Test password reset token validation with invalid token"""
        response = await client.get("/api/auth/validate-reset-token")

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 401
        assert data["message"] == "Invalid or expired token"

    @pytest.mark.asyncio
    async def test_validate_reset_token_internal_error(self, client: AsyncClient):
        """Test password reset token validation with internal error"""

        async def mock_verify_password_reset_token():
            return {
                "sub": "test-user-id",
                "token": "test-token",
                "email": "test@example.com",
            }

        with patch(
            "api.auth.controller.validate_password_reset_token"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Database error")
            app.dependency_overrides[verify_password_reset_token] = (
                mock_verify_password_reset_token
            )

            try:
                response = await client.get(
                    "/api/auth/validate-reset-token",
                    headers={"Authorization": "Bearer valid-reset-token"},
                )
                assert response.status_code == 500
                data = response.json()
                assert data["code"] == 500
                assert data["message"] == "Internal Server Error"
            finally:
                app.dependency_overrides.pop(verify_password_reset_token, None)

    @pytest.mark.asyncio
    async def test_reset_password_validation_error(self, client: AsyncClient):
        """Test password reset with validation error"""
        invalid_data = {"new_password": ""}

        invalid_token = "invalid-token-format"

        response = await client.post(
            "/api/auth/reset-password",
            json=invalid_data,
            headers={"Authorization": f"Bearer {invalid_token}"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 401
        assert data["message"] == "Invalid or expired token"

    @pytest.mark.asyncio
    async def test_cookie_setting_on_password_reset(self, client: AsyncClient):
        """Test that session cookie is set on successful password reset"""
        reset_data = {"new_password": "NewPassword123!"}

        async def mock_verify_password_reset_token():
            return {
                "sub": "test-user-id",
                "token": "test-token",
                "email": "test@example.com",
            }

        with patch("api.auth.controller.reset_password") as mock_reset:
            mock_reset.return_value = {
                "user": type(
                    "User",
                    (),
                    {
                        "id": "test-user-id",
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com",
                        "phone": "+1234567890",
                    },
                )(),
                "session_id": "test-session-id",
                "access_token": "test-access-token",
            }

            app.dependency_overrides[verify_password_reset_token] = (
                mock_verify_password_reset_token
            )

            try:
                response = await client.post(
                    "/api/auth/reset-password",
                    json=reset_data,
                    headers={"Authorization": "Bearer valid-reset-token"},
                )
                assert response.status_code == 200
                assert "session_id" in response.cookies
            finally:
                app.dependency_overrides.pop(verify_password_reset_token, None)