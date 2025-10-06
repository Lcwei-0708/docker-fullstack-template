import pytest
from models.users import Users
from core.security import verify_password
from unittest.mock import AsyncMock, patch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from api.account.schema import UserUpdate, PasswordChange
from utils.custom_exception import AuthenticationException, ServerException
from api.account.services import get_user_by_id, update_user_profile, change_password


class TestGetUserById:
    """Test get_user_by_id service function"""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test successful user retrieval by ID"""
        user = await get_user_by_id(test_db_session, test_user.id)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
        assert user.first_name == test_user.first_name

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, test_db_session: AsyncSession):
        """Test user retrieval with non-existent ID"""
        non_existent_id = "non-existent-id-123"
        user = await get_user_by_id(test_db_session, non_existent_id)

        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_database_error(self, test_db_session: AsyncSession):
        """Test get_user_by_id handles database errors gracefully"""
        # Mock database execute to raise an exception
        with patch.object(
            test_db_session, "execute", side_effect=SQLAlchemyError("Database error")
        ):
            with pytest.raises(SQLAlchemyError):
                await get_user_by_id(test_db_session, "test-id")


class TestUpdateUserProfile:
    """Test update_user_profile service function"""

    @pytest.mark.asyncio
    async def test_update_user_profile_success_all_fields(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test successful profile update with all fields"""
        update_data = UserUpdate(
            first_name="Updated",
            last_name="Name",
            email="updated@example.com",
            phone="+9876543210",
        )

        updated_user = await update_user_profile(
            test_db_session, test_user.id, update_data
        )

        assert updated_user is not None
        assert updated_user.id == test_user.id
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.email == "updated@example.com"
        assert updated_user.phone == "+9876543210"

    @pytest.mark.asyncio
    async def test_update_user_profile_success_partial_fields(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test successful profile update with only some fields"""
        update_data = UserUpdate(first_name="PartialUpdate")

        updated_user = await update_user_profile(
            test_db_session, test_user.id, update_data
        )

        assert updated_user is not None
        assert updated_user.first_name == "PartialUpdate"
        assert updated_user.last_name == test_user.last_name  # Unchanged
        assert updated_user.email == test_user.email  # Unchanged
        assert updated_user.phone == test_user.phone  # Unchanged

    @pytest.mark.asyncio
    async def test_update_user_profile_user_not_found(
        self, test_db_session: AsyncSession
    ):
        """Test profile update with non-existent user ID"""
        update_data = UserUpdate(first_name="Test")
        non_existent_id = "non-existent-id-123"

        updated_user = await update_user_profile(
            test_db_session, non_existent_id, update_data
        )

        assert updated_user is None

    @pytest.mark.asyncio
    async def test_update_user_profile_email_already_exists(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test profile update with email that already exists for another user"""
        # Create another user with different email
        another_user = Users(
            id="another-user-id",
            email="another@example.com",
            first_name="Another",
            last_name="User",
            phone="+1111111111",
            hash_password="hashed_password",
            status=True,
            password_reset_required=False,
        )
        test_db_session.add(another_user)
        await test_db_session.commit()

        # Try to update test_user with another_user's email
        update_data = UserUpdate(email="another@example.com")

        with pytest.raises(ValueError, match="Email already exists"):
            await update_user_profile(test_db_session, test_user.id, update_data)

    @pytest.mark.asyncio
    async def test_update_user_profile_same_email(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test profile update with same email (should succeed)"""
        update_data = UserUpdate(email=test_user.email)  # Same email

        updated_user = await update_user_profile(
            test_db_session, test_user.id, update_data
        )

        assert updated_user is not None
        assert updated_user.email == test_user.email

    @pytest.mark.asyncio
    async def test_update_user_profile_database_commit_error(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test profile update handles database commit errors"""
        update_data = UserUpdate(first_name="Test")

        # Mock commit to raise an exception
        with patch.object(
            test_db_session, "commit", side_effect=SQLAlchemyError("Commit error")
        ):
            with pytest.raises(SQLAlchemyError):
                await update_user_profile(test_db_session, test_user.id, update_data)


class TestChangePassword:
    """Test change_password service function"""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test successful password change"""
        password_data = PasswordChange(
            current_password="TestPassword123!",
            new_password="NewPassword123!",
            logout_all_devices=False,
        )

        mock_redis = AsyncMock()

        success = await change_password(
            test_db_session, test_user.id, password_data, mock_redis
        )

        assert success is True

        # Verify password was actually changed
        await test_db_session.refresh(test_user)
        assert await verify_password("NewPassword123!", test_user.hash_password)
        assert not await verify_password("TestPassword123!", test_user.hash_password)
        assert test_user.password_reset_required is False

    @pytest.mark.asyncio
    async def test_change_password_with_logout_all_devices(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test password change with logout all devices enabled"""
        password_data = PasswordChange(
            current_password="TestPassword123!",
            new_password="NewPassword123!",
            logout_all_devices=True,
        )

        mock_redis = AsyncMock()

        with patch(
            "api.account.services.clear_user_all_sessions", new_callable=AsyncMock
        ) as mock_clear_sessions:
            success = await change_password(
                test_db_session, test_user.id, password_data, mock_redis
            )

            assert success is True
            mock_clear_sessions.assert_called_once_with(
                test_db_session, mock_redis, test_user.id
            )

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_password(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test password change with incorrect current password"""
        password_data = PasswordChange(
            current_password="WrongPassword123!",
            new_password="NewPassword123!",
            logout_all_devices=False,
        )

        mock_redis = AsyncMock()

        with pytest.raises(
            AuthenticationException, match="Current password is incorrect"
        ):
            await change_password(
                test_db_session, test_user.id, password_data, mock_redis
            )

    @pytest.mark.asyncio
    async def test_change_password_user_not_found(self, test_db_session: AsyncSession):
        """Test password change with non-existent user ID"""
        password_data = PasswordChange(
            current_password="TestPassword123!",
            new_password="NewPassword123!",
            logout_all_devices=False,
        )

        mock_redis = AsyncMock()
        non_existent_id = "non-existent-id-123"

        success = await change_password(
            test_db_session, non_existent_id, password_data, mock_redis
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_change_password_database_error(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test password change handles database errors"""
        password_data = PasswordChange(
            current_password="TestPassword123!",
            new_password="NewPassword123!",
            logout_all_devices=False,
        )

        mock_redis = AsyncMock()

        # Mock commit to raise an exception
        with patch.object(
            test_db_session, "commit", side_effect=SQLAlchemyError("Commit error")
        ):
            with pytest.raises(ServerException, match="Failed to change password"):
                await change_password(
                    test_db_session, test_user.id, password_data, mock_redis
                )

    @pytest.mark.asyncio
    async def test_change_password_authentication_exception_propagation(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test that AuthenticationException is properly propagated"""
        password_data = PasswordChange(
            current_password="WrongPassword123!",
            new_password="NewPassword123!",
            logout_all_devices=False,
        )

        mock_redis = AsyncMock()

        # Should raise AuthenticationException, not ServerException
        with pytest.raises(AuthenticationException):
            await change_password(
                test_db_session, test_user.id, password_data, mock_redis
            )


class TestServiceIntegration:
    """Test service layer integration scenarios"""

    @pytest.mark.asyncio
    async def test_update_profile_then_change_password(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test updating profile then changing password in sequence"""
        # First update profile
        profile_update = UserUpdate(first_name="Updated", email="updated@example.com")
        updated_user = await update_user_profile(
            test_db_session, test_user.id, profile_update
        )

        assert updated_user.first_name == "Updated"
        assert updated_user.email == "updated@example.com"

        # Then change password
        password_data = PasswordChange(
            current_password="TestPassword123!",
            new_password="NewPassword123!",
            logout_all_devices=False,
        )

        mock_redis = AsyncMock()
        success = await change_password(
            test_db_session, test_user.id, password_data, mock_redis
        )

        assert success is True

        # Verify both changes were applied
        await test_db_session.refresh(updated_user)
        assert updated_user.first_name == "Updated"
        assert updated_user.email == "updated@example.com"
        assert await verify_password("NewPassword123!", updated_user.hash_password)

    @pytest.mark.asyncio
    async def test_get_user_after_profile_update(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test getting user after profile update reflects changes"""
        # Update profile
        update_data = UserUpdate(first_name="UpdatedName", last_name="UpdatedLastName")
        await update_user_profile(test_db_session, test_user.id, update_data)

        # Get user and verify changes
        user = await get_user_by_id(test_db_session, test_user.id)

        assert user.first_name == "UpdatedName"
        assert user.last_name == "UpdatedLastName"
        assert user.email == test_user.email  # Unchanged

    @pytest.mark.asyncio
    async def test_concurrent_profile_updates(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test handling of concurrent profile updates"""
        # Simulate two concurrent updates
        update1 = UserUpdate(first_name="Update1")
        update2 = UserUpdate(last_name="Update2")

        # Apply updates sequentially (in real scenario, these might be concurrent)
        user1 = await update_user_profile(test_db_session, test_user.id, update1)
        user2 = await update_user_profile(test_db_session, test_user.id, update2)

        # Both should succeed
        assert user1 is not None
        assert user2 is not None

        # Final state should reflect both changes
        final_user = await get_user_by_id(test_db_session, test_user.id)
        assert final_user.first_name == "Update1"
        assert final_user.last_name == "Update2"


class TestServiceErrorHandling:
    """Test service layer error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_update_profile_with_none_values(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test profile update with None values (should be ignored)"""
        update_data = UserUpdate(
            first_name="Updated"
            # Don't set other fields to None explicitly, just omit them
        )

        updated_user = await update_user_profile(
            test_db_session, test_user.id, update_data
        )

        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == test_user.last_name  # Unchanged
        assert updated_user.email == test_user.email  # Unchanged
        assert updated_user.phone == test_user.phone  # Unchanged

    @pytest.mark.asyncio
    async def test_change_password_with_none_redis_client(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        """Test password change with None redis client (should still work)"""
        password_data = PasswordChange(
            current_password="TestPassword123!",
            new_password="NewPassword123!",
            logout_all_devices=True,  # This should be ignored if redis_client is None
        )

        success = await change_password(
            test_db_session, test_user.id, password_data, None
        )

        assert success is True
        await test_db_session.refresh(test_user)
        assert await verify_password("NewPassword123!", test_user.hash_password)

    @pytest.mark.asyncio
    async def test_service_functions_with_invalid_user_id_format(
        self, test_db_session: AsyncSession
    ):
        """Test service functions with invalid user ID formats"""
        invalid_ids = ["", None, "   ", "invalid-format-with-special-chars!@#"]

        for invalid_id in invalid_ids:
            if invalid_id is None:
                continue  # Skip None as it will cause different errors

            # Test get_user_by_id
            user = await get_user_by_id(test_db_session, invalid_id)
            assert user is None

            # Test update_user_profile
            update_data = UserUpdate(first_name="Test")
            updated_user = await update_user_profile(
                test_db_session, invalid_id, update_data
            )
            assert updated_user is None

            # Test change_password
            password_data = PasswordChange(
                current_password="TestPassword123!",
                new_password="NewPassword123!",
                logout_all_devices=False,
            )
            mock_redis = AsyncMock()
            success = await change_password(
                test_db_session, invalid_id, password_data, mock_redis
            )
            assert success is False
