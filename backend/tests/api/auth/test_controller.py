import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from api.auth.schema import (
    ActionRequiredResponse,
)
from utils.custom_exception import (
    ConflictException,
    AuthenticationException,
    PasswordResetRequiredException,
    NotFoundException,
    SMTPNotConfiguredException,
    ValidationException,
    EmailVerificationRequiredException,
    RegistrationDisabledException,
)
from core.security import (
    verify_password_reset_token,
    verify_token,
    verify_email_verification_token,
)
from core.redis import get_redis
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
                "csrf_token": "test-csrf-token",
            }

            response = await client.post("/api/auth/register", json=register_data)

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "User registered successfully"
            assert "session_id" in response.cookies
            assert "csrf_token" in response.cookies

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
    async def test_register_email_verification_required(self, client: AsyncClient):
        """Test registration requires email verification"""
        register_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "password": "TestPassword123!",
        }

        with patch("api.auth.controller.register") as mock_register:
            mock_register.side_effect = EmailVerificationRequiredException(
                "Email verification required"
            )

            response = await client.post("/api/auth/register", json=register_data)

            assert response.status_code == 202
            data = response.json()
            assert data["code"] == 202
            assert data["message"] == "Email verification required"

    @pytest.mark.asyncio
    async def test_register_disabled(self, client: AsyncClient):
        """Test registration when registration is disabled"""
        register_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "password": "TestPassword123!",
        }

        with patch("api.auth.controller.register") as mock_register:
            mock_register.side_effect = RegistrationDisabledException("Registration is disabled")

            response = await client.post("/api/auth/register", json=register_data)

            assert response.status_code == 503
            data = response.json()
            assert data["code"] == 503
            assert data["message"] == "Registration is disabled"

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
                "csrf_token": "test-csrf-token",
            }

            response = await client.post("/api/auth/login", json=login_data)

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "User logged in successfully"
            assert "session_id" in response.cookies
            assert "csrf_token" in response.cookies

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
        with patch("api.auth.controller.verify_csrf_token") as mock_verify_csrf, patch(
            "api.auth.controller.token"
        ) as mock_token:
            mock_verify_csrf.return_value = "test-session-id"
            mock_token.return_value = "new-access-token"

            response = await client.post(
                "/api/auth/token",
                cookies={"session_id": "test-session-id"},
                headers={"X-CSRF-Token": "test-csrf-token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "Token refreshed successfully"
            assert data["data"]["access_token"] == "new-access-token"

    @pytest.mark.asyncio
    async def test_token_refresh_no_csrf_header(self, client: AsyncClient):
        """Test token refresh without CSRF header"""
        response = await client.post(
            "/api/auth/token",
            cookies={"session_id": "test-session-id"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 401
        assert data["message"] == "Invalid or expired CSRF token"

    @pytest.mark.asyncio
    async def test_token_refresh_invalid_csrf(self, client: AsyncClient):
        """Test token refresh with invalid CSRF token"""
        with patch("api.auth.controller.verify_csrf_token") as mock_verify_csrf:
            mock_verify_csrf.side_effect = AuthenticationException(
                "Invalid or expired CSRF token"
            )

            response = await client.post(
                "/api/auth/token",
                cookies={"session_id": "test-session-id"},
                headers={"X-CSRF-Token": "invalid-csrf-token"},
            )

            assert response.status_code == 401
            data = response.json()
            assert data["code"] == 401
            assert data["message"] == "Invalid or expired CSRF token"

    @pytest.mark.asyncio
    async def test_token_refresh_invalid_session(self, client: AsyncClient):
        """Test token refresh with invalid session"""
        with patch("api.auth.controller.verify_csrf_token") as mock_verify_csrf, patch(
            "api.auth.controller.token"
        ) as mock_token:
            mock_verify_csrf.return_value = "other-session-id"

            response = await client.post(
                "/api/auth/token",
                cookies={"session_id": "invalid-session-id"},
                headers={"X-CSRF-Token": "test-csrf-token"},
            )

            assert response.status_code == 401
            data = response.json()
            assert data["code"] == 401
            assert data["message"] == "Invalid or expired session"
            mock_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_token_refresh_user_not_found(self, client: AsyncClient):
        """Test token refresh with user not found"""
        with patch("api.auth.controller.verify_csrf_token") as mock_verify_csrf, patch(
            "api.auth.controller.token"
        ) as mock_token:
            mock_verify_csrf.return_value = "test-session-id"
            mock_token.side_effect = NotFoundException("User not found")

            response = await client.post(
                "/api/auth/token",
                cookies={"session_id": "test-session-id"},
                headers={"X-CSRF-Token": "test-csrf-token"},
            )

            assert response.status_code == 401
            data = response.json()
            assert data["code"] == 401
            assert data["message"] == "Invalid or expired session"

    @pytest.mark.asyncio
    async def test_token_refresh_server_error(self, client: AsyncClient):
        """Test token refresh with server error"""
        with patch("api.auth.controller.verify_csrf_token") as mock_verify_csrf, patch(
            "api.auth.controller.token"
        ) as mock_token:
            mock_verify_csrf.return_value = "test-session-id"
            mock_token.side_effect = Exception("Database error")

            response = await client.post(
                "/api/auth/token",
                cookies={"session_id": "test-session-id"},
                headers={"X-CSRF-Token": "test-csrf-token"},
            )

            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_csrf_token_success(self, client: AsyncClient):
        """Test successful CSRF token retrieval"""
        with patch("api.auth.controller.get_or_create_csrf_token") as mock_get_csrf:
            mock_get_csrf.return_value = "test-csrf-token"

            response = await client.post(
                "/api/auth/csrf-token",
                cookies={"session_id": "test-session-id"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "CSRF token retrieved successfully"
            assert data["data"]["csrf_token"] == "test-csrf-token"
            assert "csrf_token" in response.cookies

    @pytest.mark.asyncio
    async def test_csrf_token_no_session(self, client: AsyncClient):
        """Test CSRF token retrieval without session cookie"""
        response = await client.post("/api/auth/csrf-token")

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 401
        assert data["message"] == "Invalid or expired session"

    @pytest.mark.asyncio
    async def test_login_password_reset_required(self, client: AsyncClient):
        """Test login with password reset required"""
        login_data = {"email": "reset@example.com", "password": "TestPassword123!"}

        with patch("api.auth.controller.login") as mock_login:
            details = ActionRequiredResponse(
                action_type="password_reset",
                token="test-reset-token",
                expires_at="2024-01-01T00:00:00Z",
            )
            mock_exception = PasswordResetRequiredException("Password reset required")
            mock_exception.details = details
            mock_login.side_effect = mock_exception

            response = await client.post("/api/auth/login", json=login_data)
            assert response.status_code == 202
            data = response.json()
            assert data["code"] == 202
            assert data["message"] == "Password reset required"
            assert data["data"]["action_type"] == "password_reset"
            assert data["data"]["token"] == "test-reset-token"

    @pytest.mark.asyncio
    async def test_login_email_verification_required(self, client: AsyncClient):
        """Test login with email verification required"""
        login_data = {"email": "verify@example.com", "password": "TestPassword123!"}

        with patch("api.auth.controller.login") as mock_login:
            mock_exception = EmailVerificationRequiredException("Email verification required")
            mock_exception.details = {
                "action_type": "email_verification",
                "token": None,
                "expires_at": "2024-01-01T00:00:00Z",
            }
            mock_login.side_effect = mock_exception

            response = await client.post("/api/auth/login", json=login_data)
            assert response.status_code == 202
            data = response.json()
            assert data["code"] == 202
            assert data["message"] == "Email verification required"
            assert data["data"]["action_type"] == "email_verification"

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
                "csrf_token": "test-csrf-token",
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
    async def test_reset_password_authentication_exception(self, client: AsyncClient):
        """Test password reset with authentication exception"""
        reset_data = {"new_password": "NewPassword123!"}

        async def mock_verify_password_reset_token():
            return {
                "sub": "test-user-id",
                "token": "test-token",
                "email": "test@example.com",
            }

        with patch("api.auth.controller.reset_password") as mock_reset:
            mock_reset.side_effect = AuthenticationException("Invalid or expired token")
            app.dependency_overrides[verify_password_reset_token] = (
                mock_verify_password_reset_token
            )

            try:
                response = await client.post(
                    "/api/auth/reset-password",
                    json=reset_data,
                    headers={"Authorization": "Bearer valid-reset-token"},
                )
                assert response.status_code == 401
                data = response.json()
                assert data["code"] == 401
                assert data["message"] == "Invalid or expired token"
            finally:
                app.dependency_overrides.pop(verify_password_reset_token, None)

    @pytest.mark.asyncio
    async def test_reset_password_server_error(self, client: AsyncClient):
        """Test password reset with server error"""
        reset_data = {"new_password": "NewPassword123!"}

        async def mock_verify_password_reset_token():
            return {
                "sub": "test-user-id",
                "token": "test-token",
                "email": "test@example.com",
            }

        with patch("api.auth.controller.reset_password") as mock_reset:
            mock_reset.side_effect = Exception("Database error")
            app.dependency_overrides[verify_password_reset_token] = (
                mock_verify_password_reset_token
            )

            try:
                response = await client.post(
                    "/api/auth/reset-password",
                    json=reset_data,
                    headers={"Authorization": "Bearer valid-reset-token"},
                )
                assert response.status_code == 500
                data = response.json()
                assert data["code"] == 500
                assert data["message"] == "Internal Server Error"
            finally:
                app.dependency_overrides.pop(verify_password_reset_token, None)

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
                "csrf_token": "test-csrf-token",
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
                assert "csrf_token" in response.cookies
            finally:
                app.dependency_overrides.pop(verify_password_reset_token, None)

    @pytest.mark.asyncio
    async def test_forgot_password_send_email_success(self, client: AsyncClient):
        """Test forgot password sends reset email"""
        req_data = {"email": "john.doe@example.com"}
        with patch("api.auth.controller.forgot_password", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"reset_url": "http://localhost:3000/reset-password?token=test"}

            response = await client.post("/api/auth/forgot-password", json=req_data)
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "Reset password email sent"
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_forgot_password_user_not_found(self, client: AsyncClient):
        """Test forgot password returns error if user not found"""
        req_data = {"email": "not-exist@example.com"}
        with patch("api.auth.controller.forgot_password", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = NotFoundException("User not found")

            response = await client.post("/api/auth/forgot-password", json=req_data)
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 404
            assert data["message"] == "User not registered"

    @pytest.mark.asyncio
    async def test_forgot_password_cooldown_active(self, client: AsyncClient):
        """Test forgot password returns 400 when cooldown is active"""
        req_data = {"email": "john.doe@example.com"}
        with patch("api.auth.controller.forgot_password", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = ValidationException(
                "Please wait 60 seconds before requesting another password reset email",
                details={"cooldown_seconds": 60}
            )

            response = await client.post("/api/auth/forgot-password", json=req_data)
            assert response.status_code == 400
            data = response.json()
            assert data["code"] == 400
            assert data["message"] == "Please wait before requesting another password reset email"

    @pytest.mark.asyncio
    async def test_forgot_password_account_disabled(self, client: AsyncClient):
        """Test forgot password returns 403 when account is disabled"""
        req_data = {"email": "disabled@example.com"}
        with patch("api.auth.controller.forgot_password", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = AuthenticationException("Account is disabled")

            response = await client.post("/api/auth/forgot-password", json=req_data)
            assert response.status_code == 403
            data = response.json()
            assert data["code"] == 403
            assert data["message"] == "Account is disabled"

    @pytest.mark.asyncio
    async def test_forgot_password_smtp_disabled(self, client: AsyncClient):
        """Test forgot password returns 503 if SMTP disabled"""
        req_data = {"email": "john.doe@example.com"}
        with patch("api.auth.controller.forgot_password", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = SMTPNotConfiguredException("SMTP is disabled")
            response = await client.post("/api/auth/forgot-password", json=req_data)
            assert response.status_code == 503
            data = response.json()
            assert data["code"] == 503
            assert data["message"] == "SMTP is disabled"
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_password_reset_cooldown_success(self, client: AsyncClient):
        """Test get password reset cooldown returns remaining time"""
        with patch("api.auth.controller.get_password_reset_cooldown", new_callable=AsyncMock) as mock_cooldown:
            mock_cooldown.return_value = {"cooldown_seconds": 120}

            response = await client.get("/api/auth/forgot-password/cooldown?email=test@example.com")
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "Cooldown status retrieved"
            assert data["data"]["cooldown_seconds"] == 120
            mock_cooldown.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_password_reset_cooldown_no_cooldown(self, client: AsyncClient):
        """Test get password reset cooldown returns 0 when no cooldown"""
        with patch("api.auth.controller.get_password_reset_cooldown", new_callable=AsyncMock) as mock_cooldown:
            mock_cooldown.return_value = {"cooldown_seconds": 0}

            response = await client.get("/api/auth/forgot-password/cooldown?email=test@example.com")
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["cooldown_seconds"] == 0

    @pytest.mark.asyncio
    async def test_get_password_reset_cooldown_server_error(self, client: AsyncClient):
        """Test get password reset cooldown with server error"""
        with patch("api.auth.controller.get_password_reset_cooldown", new_callable=AsyncMock) as mock_cooldown:
            mock_cooldown.side_effect = Exception("Redis error")
            response = await client.get("/api/auth/forgot-password/cooldown?email=test@example.com")
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_verify_email_success(self, client: AsyncClient):
        """Test verify email success"""
        async def mock_verify_email_token():
            return {
                "sub": "test-user-id",
                "token": "test-token",
                "email": "john.doe@example.com",
                "verification_type": "registration",
            }

        with patch("api.auth.controller.verify_email") as mock_verify:
            mock_verify.return_value = {
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
                "csrf_token": "test-csrf-token",
            }
            app.dependency_overrides[verify_email_verification_token] = (
                mock_verify_email_token
            )

            try:
                response = await client.get(
                    "/api/auth/verify-email",
                    headers={"Authorization": "Bearer valid-verify-token"},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 200
                assert data["message"] == "Email verified successfully"
                assert "session_id" in response.cookies
                assert "csrf_token" in response.cookies
            finally:
                app.dependency_overrides.pop(verify_email_verification_token, None)

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, client: AsyncClient):
        """Test verify email with invalid token"""
        response = await client.get("/api/auth/verify-email")
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == 401
        assert data["message"] == "Invalid or expired token"

    @pytest.mark.asyncio
    async def test_verify_email_user_not_found(self, client: AsyncClient):
        """Test verify email when user not found"""
        async def mock_verify_email_token():
            return {
                "sub": "test-user-id",
                "token": "test-token",
                "email": "john.doe@example.com",
                "verification_type": "registration",
            }

        with patch("api.auth.controller.verify_email") as mock_verify:
            mock_verify.side_effect = NotFoundException("User not found")
            app.dependency_overrides[verify_email_verification_token] = (
                mock_verify_email_token
            )
            try:
                response = await client.get(
                    "/api/auth/verify-email",
                    headers={"Authorization": "Bearer valid-verify-token"},
                )
                assert response.status_code == 404
                data = response.json()
                assert data["code"] == 404
                assert data["message"] == "User not found"
            finally:
                app.dependency_overrides.pop(verify_email_verification_token, None)

    @pytest.mark.asyncio
    async def test_verify_email_conflict(self, client: AsyncClient):
        """Test verify email when email already exists"""
        async def mock_verify_email_token():
            return {
                "sub": "test-user-id",
                "token": "test-token",
                "email": "john.doe@example.com",
                "verification_type": "email_change",
            }

        with patch("api.auth.controller.verify_email") as mock_verify:
            mock_verify.side_effect = ConflictException("Email already exists")
            app.dependency_overrides[verify_email_verification_token] = (
                mock_verify_email_token
            )
            try:
                response = await client.get(
                    "/api/auth/verify-email",
                    headers={"Authorization": "Bearer valid-verify-token"},
                )
                assert response.status_code == 409
                data = response.json()
                assert data["code"] == 409
                assert data["message"] == "Email already exists"
            finally:
                app.dependency_overrides.pop(verify_email_verification_token, None)

    @pytest.mark.asyncio
    async def test_verify_email_server_error(self, client: AsyncClient):
        """Test verify email with server error"""
        async def mock_verify_email_token():
            return {
                "sub": "test-user-id",
                "token": "test-token",
                "email": "john.doe@example.com",
                "verification_type": "registration",
            }

        with patch("api.auth.controller.verify_email") as mock_verify:
            mock_verify.side_effect = Exception("Database error")
            app.dependency_overrides[verify_email_verification_token] = (
                mock_verify_email_token
            )
            try:
                response = await client.get(
                    "/api/auth/verify-email",
                    headers={"Authorization": "Bearer valid-verify-token"},
                )
                assert response.status_code == 500
                data = response.json()
                assert data["code"] == 500
                assert data["message"] == "Internal Server Error"
            finally:
                app.dependency_overrides.pop(verify_email_verification_token, None)

    @pytest.mark.asyncio
    async def test_resend_verification_email_success(self, client: AsyncClient):
        """Test resend verification email success"""
        req_data = {"email": "john.doe@example.com"}
        with patch("api.auth.controller.resend_verification_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"message": "Verification email sent"}
            response = await client.post("/api/auth/resend-verification", json=req_data)
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "Verification email sent"
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_resend_verification_email_cooldown(self, client: AsyncClient):
        """Test resend verification email with cooldown"""
        req_data = {"email": "john.doe@example.com"}
        with patch("api.auth.controller.resend_verification_email", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = ValidationException("Please wait")
            response = await client.post("/api/auth/resend-verification", json=req_data)
            assert response.status_code == 400
            data = response.json()
            assert data["code"] == 400
            assert data["message"] == "Please wait before requesting another verification email"

    @pytest.mark.asyncio
    async def test_resend_verification_email_disabled_account(self, client: AsyncClient):
        """Test resend verification email with disabled account"""
        req_data = {"email": "disabled@example.com"}
        with patch("api.auth.controller.resend_verification_email", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = AuthenticationException("Account is disabled")
            response = await client.post("/api/auth/resend-verification", json=req_data)
            assert response.status_code == 403
            data = response.json()
            assert data["code"] == 403
            assert data["message"] == "Account is disabled"

    @pytest.mark.asyncio
    async def test_resend_verification_email_not_found(self, client: AsyncClient):
        """Test resend verification email when user not found"""
        req_data = {"email": "missing@example.com"}
        with patch("api.auth.controller.resend_verification_email", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = NotFoundException("User not registered")
            response = await client.post("/api/auth/resend-verification", json=req_data)
            assert response.status_code == 404
            data = response.json()
            assert data["code"] == 404
            assert data["message"] == "User not registered"

    @pytest.mark.asyncio
    async def test_resend_verification_email_smtp_disabled(self, client: AsyncClient):
        """Test resend verification email when SMTP disabled"""
        req_data = {"email": "john.doe@example.com"}
        with patch("api.auth.controller.resend_verification_email", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = SMTPNotConfiguredException("SMTP is disabled")
            response = await client.post("/api/auth/resend-verification", json=req_data)
            assert response.status_code == 503
            data = response.json()
            assert data["code"] == 503
            assert data["message"] == "SMTP is disabled"

    @pytest.mark.asyncio
    async def test_resend_verification_email_server_error(self, client: AsyncClient):
        """Test resend verification email with server error"""
        req_data = {"email": "john.doe@example.com"}
        with patch("api.auth.controller.resend_verification_email", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("Database error")
            response = await client.post("/api/auth/resend-verification", json=req_data)
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_email_verification_cooldown(self, client: AsyncClient):
        """Test get email verification cooldown returns remaining time"""
        mock_redis = AsyncMock()
        mock_redis.ttl.return_value = 120
        async def override_get_redis():
            return mock_redis
        app.dependency_overrides[get_redis] = override_get_redis

        try:
            response = await client.get(
                "/api/auth/resend-verification/cooldown?email=test@example.com"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["message"] == "Cooldown status retrieved"
            assert data["data"]["cooldown_seconds"] == 120
        finally:
            app.dependency_overrides.pop(get_redis, None)

    @pytest.mark.asyncio
    async def test_get_email_verification_cooldown_server_error(self, client: AsyncClient):
        """Test get email verification cooldown with server error"""
        mock_redis = AsyncMock()
        mock_redis.ttl.side_effect = Exception("Redis error")
        async def override_get_redis():
            return mock_redis
        app.dependency_overrides[get_redis] = override_get_redis

        try:
            response = await client.get(
                "/api/auth/resend-verification/cooldown?email=test@example.com"
            )
            assert response.status_code == 500
        finally:
            app.dependency_overrides.pop(get_redis, None)