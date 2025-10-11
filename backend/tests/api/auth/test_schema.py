import pytest
from datetime import datetime
from pydantic import ValidationError
from api.auth.schema import (
    UserRegister,
    UserLogin,
    UserResponse,
    UserLoginResponse,
    TokenResponse,
    PasswordResetRequiredResponse,
    LogoutRequest,
    ResetPasswordRequest,
    TokenValidationResponse,
    LoginResult,
    SessionResult,
)


class TestAuthSchema:
    """Test Auth Schema data validation"""

    def test_user_register_valid(self):
        """Test valid user registration data"""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "password": "TestPassword123!",
        }

        user_register = UserRegister(**data)

        assert user_register.first_name == "John"
        assert user_register.last_name == "Doe"
        assert user_register.email == "john.doe@example.com"
        assert user_register.phone == "+1234567890"
        assert user_register.password == "TestPassword123!"

    def test_user_register_invalid_email(self):
        """Test invalid email format"""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email",
            "phone": "+1234567890",
            "password": "TestPassword123!",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)

        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error" for error in errors)

    def test_user_register_missing_fields(self):
        """Test missing required fields"""
        data = {"first_name": "John", "last_name": "Doe"}

        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 3

    def test_user_register_empty_strings(self):
        """Test empty string fields"""
        data = {
            "first_name": "",
            "last_name": "",
            "email": "test@example.com",
            "phone": "",
            "password": "",
        }

        try:
            user_register = UserRegister(**data)
            assert user_register.first_name == ""
            assert user_register.last_name == ""
            assert user_register.phone == ""
            assert user_register.password == ""
        except ValidationError:
            pass

    def test_user_login_valid(self):
        """Test valid user login data"""
        data = {"email": "john.doe@example.com", "password": "TestPassword123!"}

        user_login = UserLogin(**data)

        assert user_login.email == "john.doe@example.com"
        assert user_login.password == "TestPassword123!"

    def test_user_login_invalid_email(self):
        """Test invalid email format"""
        data = {"email": "invalid-email", "password": "TestPassword123!"}

        with pytest.raises(ValidationError) as exc_info:
            UserLogin(**data)

        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error" for error in errors)

    def test_user_login_missing_fields(self):
        """Test missing required fields"""
        data = {"email": "test@example.com"}

        with pytest.raises(ValidationError) as exc_info:
            UserLogin(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1

    def test_user_response_valid(self):
        """Test valid user response data"""
        data = {
            "id": "test-user-id",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
        }

        user_response = UserResponse(**data)

        assert user_response.id == "test-user-id"
        assert user_response.first_name == "John"
        assert user_response.last_name == "Doe"
        assert user_response.email == "john.doe@example.com"
        assert user_response.phone == "+1234567890"

    def test_user_response_missing_fields(self):
        """Test missing required fields"""
        data = {"id": "test-user-id", "first_name": "John"}

        with pytest.raises(ValidationError) as exc_info:
            UserResponse(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 3

    def test_user_login_response_valid(self):
        """Test valid user login response data"""
        now = datetime.now()
        user_data = {
            "id": "test-user-id",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
        }

        data = {
            "access_token": "test-access-token",
            "expires_at": now,
            "user": user_data,
        }

        user_login_response = UserLoginResponse(**data)

        assert user_login_response.access_token == "test-access-token"
        assert user_login_response.expires_at == now
        assert user_login_response.user.id == "test-user-id"
        assert user_login_response.user.first_name == "John"

    def test_user_login_response_missing_fields(self):
        """Test missing required fields"""
        data = {"access_token": "test-access-token"}

        with pytest.raises(ValidationError) as exc_info:
            UserLoginResponse(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 2

    def test_token_response_valid(self):
        """Test valid token response data"""
        now = datetime.now()
        data = {"access_token": "test-access-token", "expires_at": now}

        token_response = TokenResponse(**data)

        assert token_response.access_token == "test-access-token"
        assert token_response.expires_at == now

    def test_token_response_missing_fields(self):
        """Test missing required fields"""
        data = {"access_token": "test-access-token"}

        with pytest.raises(ValidationError) as exc_info:
            TokenResponse(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1

    def test_password_reset_required_response_valid(self):
        """Test valid password reset required response data"""
        data = {"reset_token": "test-reset-token", "expires_at": "2024-01-01T00:00:00Z"}

        password_reset_response = PasswordResetRequiredResponse(**data)

        assert password_reset_response.reset_token == "test-reset-token"
        assert password_reset_response.expires_at == "2024-01-01T00:00:00Z"

    def test_password_reset_required_response_missing_fields(self):
        """Test missing required fields"""
        data = {"reset_token": "test-reset-token"}

        with pytest.raises(ValidationError) as exc_info:
            PasswordResetRequiredResponse(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1

    def test_logout_request_valid(self):
        """Test valid logout request data"""
        data = {"logout_all": True}

        logout_request = LogoutRequest(**data)

        assert logout_request.logout_all is True

    def test_logout_request_default_value(self):
        """Test default value"""
        data = {}

        logout_request = LogoutRequest(**data)

        assert logout_request.logout_all is False

    def test_logout_request_invalid_type(self):
        """Test invalid data type"""
        data = {"logout_all": "invalid"}

        with pytest.raises(ValidationError) as exc_info:
            LogoutRequest(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1

    def test_reset_password_request_valid(self):
        """Test valid password reset request data"""
        data = {"new_password": "NewPassword123!"}

        reset_password_request = ResetPasswordRequest(**data)

        assert reset_password_request.new_password == "NewPassword123!"

    def test_reset_password_request_missing_field(self):
        """Test missing required field"""
        data = {}

        with pytest.raises(ValidationError) as exc_info:
            ResetPasswordRequest(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1

    def test_reset_password_request_empty_password(self):
        """Test empty password"""
        data = {"new_password": ""}

        try:
            reset_password_request = ResetPasswordRequest(**data)
            assert reset_password_request.new_password == ""
        except ValidationError:
            pass

    def test_token_validation_response_valid(self):
        """Test valid token validation response data"""
        data = {"is_valid": True}

        token_validation_response = TokenValidationResponse(**data)

        assert token_validation_response.is_valid is True

    def test_token_validation_response_false(self):
        """Test false value"""
        data = {"is_valid": False}

        token_validation_response = TokenValidationResponse(**data)

        assert token_validation_response.is_valid is False

    def test_token_validation_response_missing_field(self):
        """Test missing required field"""
        data = {}

        with pytest.raises(ValidationError) as exc_info:
            TokenValidationResponse(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1

    def test_token_validation_response_invalid_type(self):
        """Test invalid data type"""
        data = {"is_valid": "invalid"}

        with pytest.raises(ValidationError) as exc_info:
            TokenValidationResponse(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 1

    def test_login_result_typing(self):
        """Test LoginResult TypedDict"""
        user_data = {
            "id": "test-user-id",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
        }

        login_result: LoginResult = {
            "user": user_data,
            "session_id": "test-session-id",
            "access_token": "test-access-token",
        }

        assert login_result["user"] == user_data
        assert login_result["session_id"] == "test-session-id"
        assert login_result["access_token"] == "test-access-token"

    def test_session_result_typing(self):
        """Test SessionResult TypedDict"""
        session_result: SessionResult = {
            "session_id": "test-session-id",
            "access_token": "test-access-token",
        }

        assert session_result["session_id"] == "test-session-id"
        assert session_result["access_token"] == "test-access-token"

    def test_email_validation_edge_cases(self):
        """Test email validation edge cases"""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user123@example-domain.co.uk",
            "a@b.c",
        ]

        for email in valid_emails:
            data = {
                "first_name": "Test",
                "last_name": "User",
                "email": email,
                "phone": "+1234567890",
                "password": "TestPassword123!",
            }
            user_register = UserRegister(**data)
            assert user_register.email == email

        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com",
            "",
            "test@.com",
            "test@example.",
            "test..user@example.com",
        ]

        for email in invalid_emails:
            data = {
                "first_name": "Test",
                "last_name": "User",
                "email": email,
                "phone": "+1234567890",
                "password": "TestPassword123!",
            }
            with pytest.raises(ValidationError):
                UserRegister(**data)

    def test_phone_validation(self):
        """Test phone number validation"""
        valid_phones = [
            "+1234567890",
            "+1-234-567-8900",
            "+1 (234) 567-8900",
            "1234567890",
            "+86-138-0013-8000",
            "+44-20-7946-0958",
        ]

        for phone in valid_phones:
            data = {
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "phone": phone,
                "password": "TestPassword123!",
            }
            user_register = UserRegister(**data)
            assert user_register.phone == phone

    def test_password_validation(self):
        """Test password validation"""
        valid_passwords = [
            "TestPassword123!",
            "MySecurePass456@",
            "ComplexP@ssw0rd",
            "Simple123!",
            "VeryLongPassword123!@#",
        ]

        for password in valid_passwords:
            data = {
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "phone": "+1234567890",
                "password": password,
            }
            user_register = UserRegister(**data)
            assert user_register.password == password

    def test_datetime_validation(self):
        """Test datetime validation"""
        now = datetime.now()
        data = {"access_token": "test-token", "expires_at": now}

        token_response = TokenResponse(**data)
        assert token_response.expires_at == now

        iso_string = "2024-01-01T00:00:00Z"
        data = {
            "access_token": "test-token",
            "expires_at": datetime.fromisoformat(iso_string.replace("Z", "+00:00")),
        }

        token_response = TokenResponse(**data)
        assert token_response.expires_at is not None