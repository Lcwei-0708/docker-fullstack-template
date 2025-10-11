import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import Users
from models.user_sessions import UserSessions
from models.password_reset_tokens import PasswordResetTokens
from core.security import hash_password, create_access_token
from api.auth.services import (
    register,
    login,
    logout,
    logout_all_devices,
    token,
    reset_password,
    validate_password_reset_token,
)
from api.auth.schema import UserRegister, UserLogin
from utils.custom_exception import (
    ConflictException,
    AuthenticationException,
    PasswordResetRequiredException,
    ServerException,
    NotFoundException,
)


class TestAuthService:
    """Test Auth service layer business logic"""

    @pytest.mark.asyncio
    async def test_register_success(self, test_db_session: AsyncSession):
        """Test successful user registration"""
        mock_redis = AsyncMock()
        user_data = UserRegister(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            password="TestPassword123!",
        )

        result = await register(
            test_db_session, mock_redis, user_data, "127.0.0.1", "TestAgent/1.0"
        )

        assert "user" in result
        assert "session_id" in result
        assert "access_token" in result
        assert result["user"].email == user_data.email
        assert result["user"].first_name == user_data.first_name
        assert result["user"].last_name == user_data.last_name
        assert result["user"].phone == user_data.phone

    @pytest.mark.asyncio
    async def test_register_email_already_exists(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test registration with existing email"""
        mock_redis = AsyncMock()
        user_data = UserRegister(
            first_name="Jane",
            last_name="Doe",
            email=test_user.email,
            phone="+1234567890",
            password="TestPassword123!",
        )

        with pytest.raises(ConflictException) as exc_info:
            await register(
                test_db_session, mock_redis, user_data, "127.0.0.1", "TestAgent/1.0"
            )

        assert "Email already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_success(self, test_db_session: AsyncSession, test_user: Users):
        """Test successful login"""
        mock_redis = AsyncMock()
        login_data = UserLogin(email=test_user.email, password="TestPassword123!")

        result = await login(
            test_db_session, mock_redis, login_data, "127.0.0.1", "TestAgent/1.0"
        )

        assert "user" in result
        assert "session_id" in result
        assert "access_token" in result
        assert result["user"].email == test_user.email

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, test_db_session: AsyncSession):
        """Test login with non-existent user"""
        mock_redis = AsyncMock()
        login_data = UserLogin(
            email="nonexistent@example.com", password="TestPassword123!"
        )

        with pytest.raises(AuthenticationException) as exc_info:
            await login(
                test_db_session, mock_redis, login_data, "127.0.0.1", "TestAgent/1.0"
            )

        assert "Invalid email or password" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_disabled_account(self, test_db_session: AsyncSession):
        """Test login with disabled account"""
        mock_redis = AsyncMock()

        user_id = "test-disabled-service-user"
        hashed_pwd = await hash_password("TestPassword123!")

        disabled_user = Users(
            id=user_id,
            email="disabled@example.com",
            first_name="Disabled",
            last_name="User",
            phone="+1234567890",
            hash_password=hashed_pwd,
            status=False,
            password_reset_required=False,
        )
        test_db_session.add(disabled_user)
        await test_db_session.commit()

        login_data = UserLogin(email=disabled_user.email, password="TestPassword123!")

        with pytest.raises(AuthenticationException) as exc_info:
            await login(
                test_db_session, mock_redis, login_data, "127.0.0.1", "TestAgent/1.0"
            )

        assert "Account is disabled" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_invalid_password(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test login with invalid password"""
        mock_redis = AsyncMock()
        login_data = UserLogin(email=test_user.email, password="WrongPassword123!")

        with pytest.raises(AuthenticationException) as exc_info:
            await login(
                test_db_session, mock_redis, login_data, "127.0.0.1", "TestAgent/1.0"
            )

        assert "Invalid email or password" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_login_password_reset_required(self, test_db_session: AsyncSession):
        """Test login with password reset required"""
        mock_redis = AsyncMock()

        user_id = "test-reset-service-user"
        hashed_pwd = await hash_password("TestPassword123!")

        reset_user = Users(
            id=user_id,
            email="reset@example.com",
            first_name="Reset",
            last_name="User",
            phone="+1234567890",
            hash_password=hashed_pwd,
            status=True,
            password_reset_required=True,
        )
        test_db_session.add(reset_user)
        await test_db_session.commit()

        login_data = UserLogin(email=reset_user.email, password="TestPassword123!")

        with pytest.raises(PasswordResetRequiredException) as exc_info:
            await login(
                test_db_session, mock_redis, login_data, "127.0.0.1", "TestAgent/1.0"
            )

        assert "Password reset required" in str(exc_info.value)
        assert exc_info.value.details is not None
        assert hasattr(exc_info.value.details, "reset_token")
        assert hasattr(exc_info.value.details, "expires_at")

    @pytest.mark.asyncio
    async def test_logout_success(
        self,
        test_db_session: AsyncSession,
        test_user: Users,
        test_user_session: UserSessions,
    ):
        """Test successful logout"""
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1

        result = await logout(
            test_db_session, mock_redis, test_user.id, test_user_session.id
        )

        assert result is True
        mock_redis.delete.assert_called_once_with(f"session:{test_user_session.id}")

    @pytest.mark.asyncio
    async def test_logout_all_devices_success(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test successful logout all devices"""
        mock_redis = AsyncMock()

        with patch(
            "api.auth.services.clear_user_all_sessions", return_value=True
        ) as mock_clear:
            result = await logout_all_devices(test_db_session, mock_redis, test_user.id)

            assert result is True
            mock_clear.assert_called_once_with(
                test_db_session, mock_redis, test_user.id
            )

    @pytest.mark.asyncio
    async def test_logout_all_devices_failure(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test logout all devices failure"""
        mock_redis = AsyncMock()

        with patch(
            "api.auth.services.clear_user_all_sessions",
            side_effect=ServerException("Redis error"),
        ):
            with pytest.raises(ServerException) as exc_info:
                await logout_all_devices(test_db_session, mock_redis, test_user.id)

            assert "Failed to logout all devices" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_token_refresh_success(
        self,
        test_db_session: AsyncSession,
        test_user: Users,
        test_user_session: UserSessions,
    ):
        """Test successful token refresh"""
        mock_redis = AsyncMock()
        session_data = {
            "user_id": test_user.id,
            "email": test_user.email,
            "ip_address": "127.0.0.1",
            "user_agent": "TestAgent/1.0",
            "access_token": test_user_session.jwt_access_token,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
        }
        mock_redis.get.return_value = str(session_data)
        mock_redis.setex.return_value = True

        with patch(
            "api.auth.services.extend_session_ttl", return_value=True
        ) as mock_extend:
            result = await token(test_db_session, mock_redis, test_user_session.id)

            assert result is not None
            assert isinstance(result, str)
            mock_extend.assert_called_once()

    @pytest.mark.asyncio
    async def test_token_refresh_invalid_session(self, test_db_session: AsyncSession):
        """Test token refresh with invalid session"""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with pytest.raises(AuthenticationException) as exc_info:
            await token(test_db_session, mock_redis, "invalid_session_id")

        assert "Invalid or expired session" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_token_refresh_user_not_found(self, test_db_session: AsyncSession):
        """Test token refresh with non-existent user"""
        mock_redis = AsyncMock()
        session_data = {
            "user_id": "nonexistent_user_id",
            "email": "test@example.com",
            "ip_address": "127.0.0.1",
            "user_agent": "TestAgent/1.0",
            "access_token": "test_token",
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
        }
        mock_redis.get.return_value = str(session_data)

        with pytest.raises(NotFoundException) as exc_info:
            await token(test_db_session, mock_redis, "test_session_id")

        assert "User not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_token_refresh_disabled_user(self, test_db_session: AsyncSession):
        """Test token refresh with disabled user"""
        mock_redis = AsyncMock()
        user_id = "test-disabled-token-user"
        hashed_pwd = await hash_password("TestPassword123!")

        disabled_user = Users(
            id=user_id,
            email="disabled@example.com",
            first_name="Disabled",
            last_name="User",
            phone="+1234567890",
            hash_password=hashed_pwd,
            status=False,
            password_reset_required=False,
        )
        test_db_session.add(disabled_user)
        await test_db_session.commit()

        session_data = {
            "user_id": user_id,
            "email": disabled_user.email,
            "ip_address": "127.0.0.1",
            "user_agent": "TestAgent/1.0",
            "access_token": "test_token",
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
        }
        mock_redis.get.return_value = str(session_data)

        with pytest.raises(AuthenticationException) as exc_info:
            await token(test_db_session, mock_redis, "test_session_id")

        assert "Account is disabled" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reset_password_success(self, test_db_session: AsyncSession):
        """Test successful password reset"""
        mock_redis = AsyncMock()
        user_id = "test-reset-password-service-user"
        hashed_pwd = await hash_password("OldPassword123!")

        reset_user = Users(
            id=user_id,
            email="resetpassword@example.com",
            first_name="Reset",
            last_name="Password",
            phone="+1234567890",
            hash_password=hashed_pwd,
            status=True,
            password_reset_required=True,
        )
        test_db_session.add(reset_user)
        await test_db_session.commit()

        reset_token_record = PasswordResetTokens(
            user_id=user_id,
            token="test_reset_token_123",
            is_used=False,
            expires_at=datetime.now() + timedelta(minutes=30),
        )
        test_db_session.add(reset_token_record)
        await test_db_session.commit()

        token_data = {"sub": user_id, "token": "test_reset_token_123"}

        with patch(
            "api.auth.services.clear_user_all_sessions", return_value=True
        ) as mock_clear:
            result = await reset_password(
                test_db_session,
                mock_redis,
                token_data,
                "NewPassword123!",
                "127.0.0.1",
                "TestAgent/1.0",
            )

            assert "user" in result
            assert "session_id" in result
            assert "access_token" in result
            assert result["user"].id == user_id
            assert result["user"].password_reset_required is False
            mock_clear.assert_called_once_with(test_db_session, mock_redis, user_id)

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, test_db_session: AsyncSession):
        """Test password reset with invalid token"""
        mock_redis = AsyncMock()
        token_data = {"sub": "nonexistent_user", "token": "invalid_token"}

        with pytest.raises(AuthenticationException) as exc_info:
            await reset_password(
                test_db_session,
                mock_redis,
                token_data,
                "NewPassword123!",
                "127.0.0.1",
                "TestAgent/1.0",
            )

        assert "Invalid or expired token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reset_password_user_not_found(
        self,
        test_db_session: AsyncSession,
        create_password_reset_token_with_invalid_user,
    ):
        """Test password reset with non-existent user"""
        mock_redis = AsyncMock()
        token_data = create_password_reset_token_with_invalid_user["token_data"]

        with pytest.raises(NotFoundException) as exc_info:
            await reset_password(
                test_db_session,
                mock_redis,
                token_data,
                "NewPassword123!",
                "127.0.0.1",
                "TestAgent/1.0",
            )

        assert "User not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reset_password_not_required(self, test_db_session: AsyncSession):
        """Test password reset when not required"""
        mock_redis = AsyncMock()
        user_id = "test-no-reset-user"
        hashed_pwd = await hash_password("TestPassword123!")

        no_reset_user = Users(
            id=user_id,
            email="noreset@example.com",
            first_name="No",
            last_name="Reset",
            phone="+1234567890",
            hash_password=hashed_pwd,
            status=True,
            password_reset_required=False,
        )
        test_db_session.add(no_reset_user)
        await test_db_session.commit()
        reset_token_record = PasswordResetTokens(
            user_id=user_id,
            token="test_token_123",
            is_used=False,
            expires_at=datetime.now() + timedelta(minutes=30),
        )
        test_db_session.add(reset_token_record)
        await test_db_session.commit()

        token_data = {"sub": user_id, "token": "test_token_123"}

        with pytest.raises(AuthenticationException) as exc_info:
            await reset_password(
                test_db_session,
                mock_redis,
                token_data,
                "NewPassword123!",
                "127.0.0.1",
                "TestAgent/1.0",
            )

        assert "Password reset not required for this user" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_password_reset_token_success(
        self, test_db_session: AsyncSession
    ):
        """Test successful password reset token validation"""
        user_id = "test-validate-token-service-user"
        hashed_pwd = await hash_password("TestPassword123!")

        validate_user = Users(
            id=user_id,
            email="validatetoken@example.com",
            first_name="Validate",
            last_name="Token",
            phone="+1234567890",
            hash_password=hashed_pwd,
            status=True,
            password_reset_required=True,
        )
        test_db_session.add(validate_user)
        await test_db_session.commit()
        reset_token_record = PasswordResetTokens(
            user_id=user_id,
            token="test_validate_token_123",
            is_used=False,
            expires_at=datetime.now() + timedelta(minutes=30),
        )
        test_db_session.add(reset_token_record)
        await test_db_session.commit()

        token_data = {"sub": user_id, "token": "test_validate_token_123"}

        result = await validate_password_reset_token(test_db_session, token_data)

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_password_reset_token_invalid(
        self, test_db_session: AsyncSession
    ):
        """Test validation of invalid password reset token"""
        token_data = {"sub": "nonexistent_user", "token": "invalid_token"}

        with pytest.raises(AuthenticationException) as exc_info:
            await validate_password_reset_token(test_db_session, token_data)

        assert "Invalid or expired token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_password_reset_token_user_not_found(
        self,
        test_db_session: AsyncSession,
        create_password_reset_token_with_invalid_user,
    ):
        """Test password reset token validation with non-existent user"""
        token_data = create_password_reset_token_with_invalid_user["token_data"]

        with pytest.raises(AuthenticationException) as exc_info:
            await validate_password_reset_token(test_db_session, token_data)

        assert "User not found or password reset not required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_password_reset_token_not_required(
        self, test_db_session: AsyncSession
    ):
        """Test password reset token validation when not required"""
        user_id = "test-no-reset-validate-user"
        hashed_pwd = await hash_password("TestPassword123!")

        no_reset_user = Users(
            id=user_id,
            email="noresetvalidate@example.com",
            first_name="No",
            last_name="Reset",
            phone="+1234567890",
            hash_password=hashed_pwd,
            status=True,
            password_reset_required=False,
        )
        test_db_session.add(no_reset_user)
        await test_db_session.commit()
        reset_token_record = PasswordResetTokens(
            user_id=user_id,
            token="test_token_123",
            is_used=False,
            expires_at=datetime.now() + timedelta(minutes=30),
        )
        test_db_session.add(reset_token_record)
        await test_db_session.commit()

        token_data = {"sub": user_id, "token": "test_token_123"}

        with pytest.raises(AuthenticationException) as exc_info:
            await validate_password_reset_token(test_db_session, token_data)

        assert "User not found or password reset not required" in str(exc_info.value)