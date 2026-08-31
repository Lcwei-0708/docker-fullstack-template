from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.users.schema import (
    UserCreate,
    UserDeleteBatchResponse,
    UserPagination,
    UserResponse,
    UserUpdate,
)
from api.users.services import (
    _assert_can_manage_user_role,
    _assign_user_role,
    _delete_user_related_records,
    _get_user_role_name,
    _get_user_roles_map,
    _update_user_role,
    create_user,
    delete_users,
    get_all_users,
    reset_user_password,
    update_user,
)
from models.email_verification_tokens import EmailVerificationTokens
from models.login_logs import LoginLogs
from models.password_reset_tokens import PasswordResetTokens
from models.role_mapper import RoleMapper
from models.roles import Roles
from models.user_sessions import UserSessions
from models.users import Users
from utils.custom_exception import (
    AuthorizationException,
    ConflictException,
    NotFoundException,
    ServerException,
)


class TestGetAllUsers:
    """Test get_all_users service function"""

    @pytest.mark.asyncio
    async def test_get_all_users_success(self, test_db_session: AsyncSession):
        """Test successful users retrieval"""
        # Create test users
        user1 = Users(
            id="user1",
            email="user1@example.com",
            first_name="User",
            last_name="One",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        user2 = Users(
            id="user2",
            email="user2@example.com",
            first_name="User",
            last_name="Two",
            phone="+1234567891",
            hash_password="hashed_password",
            status=False,
            created_at=datetime.now(),
        )

        test_db_session.add(user1)
        test_db_session.add(user2)
        await test_db_session.commit()

        result = await get_all_users(db=test_db_session, page=1, per_page=10)

        assert isinstance(result, UserPagination)
        assert result.total == 2
        assert len(result.users) == 2
        assert result.page == 1
        assert result.per_page == 10

    @pytest.mark.asyncio
    async def test_get_all_users_hides_super_admin_when_disabled(
        self, test_db_session: AsyncSession
    ):
        """Super-admin users are excluded when SHOW_SUPER_ADMIN is false"""
        regular = Users(
            id="user-regular",
            email="regular@example.com",
            first_name="Regular",
            last_name="User",
            phone="+1000000100",
            hash_password="hashed",
            status=True,
            created_at=datetime.now(),
        )
        super_user = Users(
            id="user-super",
            email="super@example.com",
            first_name="Super",
            last_name="Admin",
            phone="+1000000101",
            hash_password="hashed",
            status=True,
            created_at=datetime.now(),
        )
        user_role = Roles(id="role-user-list", name="user", description="", level=1)
        super_role = Roles(id="role-super-list", name="super-admin", description="", level=100)
        test_db_session.add_all([regular, super_user, user_role, super_role])
        await test_db_session.commit()
        test_db_session.add_all(
            [
                RoleMapper(user_id=regular.id, role_id=user_role.id),
                RoleMapper(user_id=super_user.id, role_id=super_role.id),
            ]
        )
        await test_db_session.commit()

        with patch("api.users.services.settings.SHOW_SUPER_ADMIN", False):
            result = await get_all_users(db=test_db_session, page=1, per_page=10)

        assert result.total == 1
        assert len(result.users) == 1
        assert result.users[0].id == "user-regular"

    @pytest.mark.asyncio
    async def test_get_all_users_shows_super_admin_when_enabled(
        self, test_db_session: AsyncSession
    ):
        """Super-admin users appear when SHOW_SUPER_ADMIN is true"""
        regular = Users(
            id="user-regular-2",
            email="regular2@example.com",
            first_name="Regular",
            last_name="Two",
            phone="+1000000102",
            hash_password="hashed",
            status=True,
            created_at=datetime.now(),
        )
        super_user = Users(
            id="user-super-2",
            email="super2@example.com",
            first_name="Super",
            last_name="Two",
            phone="+1000000103",
            hash_password="hashed",
            status=True,
            created_at=datetime.now(),
        )
        user_role = Roles(id="role-user-list-2", name="user", description="", level=1)
        super_role = Roles(id="role-super-list-2", name="super-admin", description="", level=100)
        test_db_session.add_all([regular, super_user, user_role, super_role])
        await test_db_session.commit()
        test_db_session.add_all(
            [
                RoleMapper(user_id=regular.id, role_id=user_role.id),
                RoleMapper(user_id=super_user.id, role_id=super_role.id),
            ]
        )
        await test_db_session.commit()

        with patch("api.users.services.settings.SHOW_SUPER_ADMIN", True):
            result = await get_all_users(db=test_db_session, page=1, per_page=10)

        ids = {user.id for user in result.users}
        assert result.total == 2
        assert ids == {"user-regular-2", "user-super-2"}

    @pytest.mark.asyncio
    async def test_get_all_users_with_keyword(self, test_db_session: AsyncSession):
        """Test users retrieval with keyword search"""
        user1 = Users(
            id="user1",
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        user2 = Users(
            id="user2",
            email="jane.smith@example.com",
            first_name="Jane",
            last_name="Smith",
            phone="+1234567891",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )

        test_db_session.add(user1)
        test_db_session.add(user2)
        await test_db_session.commit()

        result = await get_all_users(db=test_db_session, keyword="john", page=1, per_page=10)

        assert result.total == 1
        assert len(result.users) == 1
        assert result.users[0].first_name == "John"

    @pytest.mark.asyncio
    async def test_get_all_users_with_status_filter(self, test_db_session: AsyncSession):
        """Test users retrieval with status filter"""
        user1 = Users(
            id="user1",
            email="active@example.com",
            first_name="Active",
            last_name="User",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        user2 = Users(
            id="user2",
            email="inactive@example.com",
            first_name="Inactive",
            last_name="User",
            phone="+1234567891",
            hash_password="hashed_password",
            status=False,
            created_at=datetime.now(),
        )

        test_db_session.add(user1)
        test_db_session.add(user2)
        await test_db_session.commit()

        result = await get_all_users(db=test_db_session, status="true", page=1, per_page=10)

        assert result.total == 1
        assert len(result.users) == 1
        assert result.users[0].status

    @pytest.mark.asyncio
    async def test_get_all_users_with_role_filter(self, test_db_session: AsyncSession):
        """Test users retrieval with role filter"""
        # Create test user
        user = Users(
            id="user1",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user)
        await test_db_session.commit()

        # Create test role
        role = Roles(id="role1", name="admin", description="Administrator role")
        test_db_session.add(role)
        await test_db_session.commit()

        # Create role mapping
        role_mapping = RoleMapper(user_id="user1", role_id="role1")
        test_db_session.add(role_mapping)
        await test_db_session.commit()

        result = await get_all_users(db=test_db_session, role="admin", page=1, per_page=10)

        assert result.total == 1
        assert len(result.users) == 1
        assert result.users[0].role == "admin"

    @pytest.mark.asyncio
    async def test_get_all_users_empty_result(self, test_db_session: AsyncSession):
        """Test users retrieval with no results"""
        result = await get_all_users(db=test_db_session, page=1, per_page=10)

        assert result.total == 0
        assert len(result.users) == 0
        assert result.page == 1
        assert result.per_page == 10
        assert result.total_pages == 0

    @pytest.mark.asyncio
    async def test_get_all_users_pagination(self, test_db_session: AsyncSession):
        """Test users retrieval with pagination"""
        # Create multiple test users
        for i in range(15):
            user = Users(
                id=f"user{i}",
                email=f"user{i}@example.com",
                first_name=f"User{i}",
                last_name="Test",
                phone=f"+123456789{i}",
                hash_password="hashed_password",
                status=True,
                created_at=datetime.now(),
            )
            test_db_session.add(user)

        await test_db_session.commit()

        result = await get_all_users(db=test_db_session, page=2, per_page=10)

        assert result.total == 15
        assert len(result.users) == 5  # Second page should have 5 users
        assert result.page == 2
        assert result.per_page == 10
        assert result.total_pages == 2

    @pytest.mark.asyncio
    async def test_get_all_users_sorting(self, test_db_session: AsyncSession):
        """Test users retrieval with sorting"""
        user1 = Users(
            id="user1",
            email="a@example.com",
            first_name="A",
            last_name="User",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        user2 = Users(
            id="user2",
            email="b@example.com",
            first_name="B",
            last_name="User",
            phone="+1234567891",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )

        test_db_session.add(user1)
        test_db_session.add(user2)
        await test_db_session.commit()

        result = await get_all_users(
            db=test_db_session, sort_by="email", desc=False, page=1, per_page=10
        )

        assert len(result.users) == 2
        assert result.users[0].email == "a@example.com"
        assert result.users[1].email == "b@example.com"

        result_desc = await get_all_users(
            db=test_db_session,
            sort_by="email",
            desc=True,
            page=1,
            per_page=10,
        )
        assert result_desc.users[0].email == "b@example.com"

    @pytest.mark.asyncio
    async def test_get_all_users_sort_by_role_desc(self, test_db_session: AsyncSession):
        """Test users retrieval with role sorting desc"""
        user1 = Users(
            id="user1",
            email="a@example.com",
            first_name="A",
            last_name="User",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        user2 = Users(
            id="user2",
            email="b@example.com",
            first_name="B",
            last_name="User",
            phone="+1234567891",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        role_admin = Roles(id="role1", name="admin", description="Admin role")
        role_user = Roles(id="role2", name="user", description="User role")
        test_db_session.add_all([user1, user2, role_admin, role_user])
        await test_db_session.commit()

        test_db_session.add(RoleMapper(user_id="user1", role_id="role1"))
        test_db_session.add(RoleMapper(user_id="user2", role_id="role2"))
        await test_db_session.commit()

        result = await get_all_users(
            db=test_db_session, sort_by="role", desc=True, page=1, per_page=10
        )

        assert result.users[0].role == "user"
        assert result.users[1].role == "admin"

    @pytest.mark.asyncio
    async def test_get_all_users_sort_by_role_asc(self, test_db_session: AsyncSession):
        user1 = Users(
            id="user1",
            email="a@example.com",
            first_name="A",
            last_name="User",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        user2 = Users(
            id="user2",
            email="b@example.com",
            first_name="B",
            last_name="User",
            phone="+1234567891",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        role_admin = Roles(id="role1", name="admin", description="Admin")
        role_user = Roles(id="role2", name="user", description="User")
        test_db_session.add_all([user1, user2, role_admin, role_user])
        await test_db_session.commit()
        test_db_session.add(RoleMapper(user_id="user1", role_id="role1"))
        test_db_session.add(RoleMapper(user_id="user2", role_id="role2"))
        await test_db_session.commit()

        result = await get_all_users(
            db=test_db_session, sort_by="role", desc=False, page=1, per_page=10
        )
        assert result.users[0].role == "admin"
        assert result.users[1].role == "user"

    @pytest.mark.asyncio
    async def test_get_all_users_unknown_sort_falls_back(self, test_db_session: AsyncSession):
        user = Users(
            id="user1",
            email="a@example.com",
            first_name="A",
            last_name="User",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user)
        await test_db_session.commit()

        result = await get_all_users(
            db=test_db_session, sort_by="not_a_column", page=1, per_page=10
        )
        assert len(result.users) == 1

    @pytest.mark.asyncio
    async def test_get_all_users_multiple_status_values(self, test_db_session: AsyncSession):
        active = Users(
            id="user1",
            email="active@example.com",
            first_name="Active",
            last_name="User",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        inactive = Users(
            id="user2",
            email="inactive@example.com",
            first_name="Inactive",
            last_name="User",
            phone="+1234567891",
            hash_password="hashed_password",
            status=False,
            created_at=datetime.now(),
        )
        test_db_session.add_all([active, inactive])
        await test_db_session.commit()

        result = await get_all_users(db=test_db_session, status="true,false", page=1, per_page=10)
        assert result.total == 2

    """Test create_user service function"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, test_db_session: AsyncSession):
        """Test successful user creation"""
        user_data = UserCreate(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            password="TestPassword123!",
            status=True,
            role="admin",
        )

        with patch("api.users.services._assert_can_manage_user_role") as mock_assert_role:
            with patch("api.users.services._assign_user_role") as mock_assign_role:
                result = await create_user(test_db_session, user_data, actor_user_id="actor1")

                assert isinstance(result, UserResponse)
                assert result.email == user_data.email
                assert result.first_name == user_data.first_name
                assert result.last_name == user_data.last_name
                assert result.phone == user_data.phone
                assert result.status == user_data.status
                assert result.role == user_data.role
                mock_assert_role.assert_awaited_once()
                mock_assign_role.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_user_email_exists(self, test_db_session: AsyncSession):
        """Test user creation with existing email"""
        # Create existing user
        existing_user = Users(
            id="existing-user",
            email="existing@example.com",
            first_name="Existing",
            last_name="User",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(existing_user)
        await test_db_session.commit()

        user_data = UserCreate(
            first_name="John",
            last_name="Doe",
            email="existing@example.com",
            phone="+1234567890",
            password="TestPassword123!",
            status=True,
        )

        with pytest.raises(ConflictException) as exc_info:
            await create_user(test_db_session, user_data, actor_user_id="actor1")

        assert "Email already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_user_without_role(self, test_db_session: AsyncSession):
        """Test user creation without role assignment"""
        user_data = UserCreate(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            password="TestPassword123!",
            status=True,
        )

        result = await create_user(test_db_session, user_data, actor_user_id="actor1")

        assert isinstance(result, UserResponse)
        assert result.role is None


class TestUpdateUser:
    """Test update_user service function"""

    @pytest.mark.asyncio
    async def test_update_user_success(self, test_db_session: AsyncSession):
        """Test successful user update"""
        # Create test user
        user = Users(
            id="user1",
            email="user@example.com",
            first_name="Original",
            last_name="Name",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user)
        await test_db_session.commit()

        update_data = UserUpdate(
            first_name="Updated", last_name="Name", email="updated@example.com"
        )

        with patch("api.users.services._update_user_role") as mock_update_role:
            result = await update_user(
                test_db_session, "user1", update_data, actor_user_id="actor1"
            )

            assert isinstance(result, UserResponse)
            assert result.first_name == "Updated"
            assert result.last_name == "Name"
            assert result.email == "updated@example.com"
            mock_update_role.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_email_clears_pending_verification(
        self, test_db_session: AsyncSession
    ):
        """Admin email update should confirm the new address and clear pending verification"""
        user = Users(
            id="user1",
            email="user@example.com",
            pending_email="pending@example.com",
            email_verified=True,
            first_name="Original",
            last_name="Name",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user)
        await test_db_session.commit()

        result = await update_user(
            test_db_session,
            "user1",
            UserUpdate(email="admin-set@example.com"),
            actor_user_id="actor1",
        )

        refreshed = await test_db_session.get(Users, "user1")
        assert result.email == "admin-set@example.com"
        assert refreshed.email == "admin-set@example.com"
        assert refreshed.pending_email is None
        assert refreshed.email_verified is True

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, test_db_session: AsyncSession):
        """Test user update with non-existent user"""
        update_data = UserUpdate(first_name="Updated")

        with pytest.raises(NotFoundException) as exc_info:
            await update_user(test_db_session, "nonexistent", update_data, actor_user_id="actor1")

        assert "User not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_user_email_exists(self, test_db_session: AsyncSession):
        """Test user update with existing email"""
        # Create two users
        user1 = Users(
            id="user1",
            email="user1@example.com",
            first_name="User",
            last_name="One",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        user2 = Users(
            id="user2",
            email="user2@example.com",
            first_name="User",
            last_name="Two",
            phone="+1234567891",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user1)
        test_db_session.add(user2)
        await test_db_session.commit()

        update_data = UserUpdate(email="user2@example.com")

        with pytest.raises(ConflictException) as exc_info:
            await update_user(test_db_session, "user1", update_data, actor_user_id="actor1")

        assert "Email already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_user_with_role(self, test_db_session: AsyncSession):
        user = Users(
            id="user1",
            email="user@example.com",
            first_name="Original",
            last_name="Name",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user)
        await test_db_session.commit()

        with patch("api.users.services._assert_can_manage_user_role") as mock_assert:
            with patch("api.users.services._update_user_role") as mock_update_role:
                result = await update_user(
                    test_db_session,
                    "user1",
                    UserUpdate(role="admin"),
                    actor_user_id="actor1",
                )
        assert result.id == "user1"
        mock_assert.assert_awaited_once()
        mock_update_role.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_user_rejects_higher_role_level(self, test_db_session: AsyncSession):
        actor = Users(
            id="actor-upd",
            email="actor-upd@example.com",
            first_name="Actor",
            last_name="Upd",
            phone="+1000000011",
            hash_password="hashed",
            status=True,
            created_at=datetime.now(),
        )
        target = Users(
            id="target-upd",
            email="target-upd@example.com",
            first_name="Target",
            last_name="Upd",
            phone="+1000000012",
            hash_password="hashed",
            status=True,
            created_at=datetime.now(),
        )
        actor_role = Roles(id="role-actor-upd", name="staff", description="", level=20)
        target_role = Roles(id="role-target-upd", name="chief", description="", level=90)
        test_db_session.add_all([actor, target, actor_role, target_role])
        await test_db_session.commit()
        test_db_session.add_all(
            [
                RoleMapper(user_id=actor.id, role_id=actor_role.id),
                RoleMapper(user_id=target.id, role_id=target_role.id),
            ]
        )
        await test_db_session.commit()

        with pytest.raises(AuthorizationException) as exc_info:
            await update_user(
                test_db_session,
                "target-upd",
                UserUpdate(first_name="Hacked"),
                actor_user_id="actor-upd",
            )
        assert "higher role level" in str(exc_info.value)

    """Test delete_users service function"""

    @pytest.mark.asyncio
    async def test_delete_users_success(self, test_db_session: AsyncSession):
        """Test successful users deletion"""
        # Create test users
        user1 = Users(
            id="user1",
            email="user1@example.com",
            first_name="User",
            last_name="One",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        user2 = Users(
            id="user2",
            email="user2@example.com",
            first_name="User",
            last_name="Two",
            phone="+1234567891",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user1)
        test_db_session.add(user2)
        await test_db_session.commit()

        mock_redis = AsyncMock()

        with (
            patch("api.users.services.clear_user_all_sessions") as mock_clear_sessions,
            patch("api.users.services._delete_user_related_records") as mock_delete_related,
        ):
            result = await delete_users(test_db_session, mock_redis, ["user1", "user2"])

            assert isinstance(result, UserDeleteBatchResponse)
            assert result.total_users == 2
            assert result.success_count == 2
            assert result.failed_count == 0
            assert len(result.results) == 2
            assert all(r.status == "success" for r in result.results)
            mock_clear_sessions.assert_called()
            mock_delete_related.assert_called()

    @pytest.mark.asyncio
    async def test_delete_users_rejects_super_admin(self, test_db_session: AsyncSession):
        """Test deleting a system super-admin user is rejected"""
        user = Users(
            id="super1",
            email="super@example.com",
            first_name="Super",
            last_name="Admin",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        role = Roles(id="role-super", name="super-admin", description="System super-admin")
        mapping = RoleMapper(user_id="super1", role_id="role-super")
        test_db_session.add(user)
        test_db_session.add(role)
        test_db_session.add(mapping)
        await test_db_session.commit()

        mock_redis = AsyncMock()
        result = await delete_users(test_db_session, mock_redis, ["super1"])

        assert result.total_users == 1
        assert result.success_count == 0
        assert result.failed_count == 1
        assert result.results[0].status == "failed"
        assert "Cannot delete a system super-admin user" in result.results[0].message

        remaining = await test_db_session.get(Users, "super1")
        assert remaining is not None

    @pytest.mark.asyncio
    async def test_delete_users_partial_success(self, test_db_session: AsyncSession):
        """Test users deletion with partial success"""
        # Create one user
        user = Users(
            id="user1",
            email="user1@example.com",
            first_name="User",
            last_name="One",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user)
        await test_db_session.commit()

        mock_redis = AsyncMock()

        with (
            patch("api.users.services.clear_user_all_sessions"),
            patch("api.users.services._delete_user_related_records"),
        ):
            result = await delete_users(test_db_session, mock_redis, ["user1", "nonexistent"])

            assert isinstance(result, UserDeleteBatchResponse)
            assert result.total_users == 2
            assert result.success_count == 1
            assert result.failed_count == 1
            assert len(result.results) == 2

            # Check individual results
            success_results = [r for r in result.results if r.status == "success"]
            failed_results = [r for r in result.results if r.status == "failed"]

            assert len(success_results) == 1
            assert len(failed_results) == 1
            assert success_results[0].user_id == "user1"
            assert failed_results[0].user_id == "nonexistent"
            assert "User not found" in failed_results[0].message

    @pytest.mark.asyncio
    async def test_delete_users_all_failed(self, test_db_session: AsyncSession):
        """Test users deletion with all failed"""
        mock_redis = AsyncMock()

        result = await delete_users(test_db_session, mock_redis, ["nonexistent1", "nonexistent2"])

        assert isinstance(result, UserDeleteBatchResponse)
        assert result.total_users == 2
        assert result.success_count == 0
        assert result.failed_count == 2
        assert len(result.results) == 2
        assert all(r.status == "failed" for r in result.results)
        assert all("User not found" in r.message for r in result.results)

    @pytest.mark.asyncio
    async def test_delete_users_with_session_clear_failure(self, test_db_session: AsyncSession):
        """Test users deletion when session clearing fails"""
        # Create test user
        user = Users(
            id="user1",
            email="user1@example.com",
            first_name="User",
            last_name="One",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user)
        await test_db_session.commit()

        mock_redis = AsyncMock()

        with (
            patch("api.users.services.clear_user_all_sessions") as mock_clear_sessions,
            patch("api.users.services._delete_user_related_records"),
        ):
            mock_clear_sessions.side_effect = Exception("Redis connection failed")

            result = await delete_users(test_db_session, mock_redis, ["user1"])

            assert isinstance(result, UserDeleteBatchResponse)
            assert result.total_users == 1
            assert result.success_count == 0
            assert result.failed_count == 1
            assert result.results[0].status == "failed"
            assert "Failed to delete user" in result.results[0].message

    @pytest.mark.asyncio
    async def test_delete_users_with_foreign_key_constraints(self, test_db_session: AsyncSession):
        """Test users deletion with foreign key constraints handling"""
        # Create test user
        user = Users(
            id="user1",
            email="user1@example.com",
            first_name="User",
            last_name="One",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user)
        await test_db_session.commit()

        mock_redis = AsyncMock()

        with (
            patch("api.users.services.clear_user_all_sessions"),
            patch("api.users.services._delete_user_related_records") as mock_delete_related,
        ):
            result = await delete_users(test_db_session, mock_redis, ["user1"])

            assert isinstance(result, UserDeleteBatchResponse)
            assert result.total_users == 1
            assert result.success_count == 1
            assert result.failed_count == 0
            assert result.results[0].status == "success"
            assert result.results[0].user_id == "user1"

            # Verify that related records deletion was called
            mock_delete_related.assert_called_once_with(test_db_session, "user1")

    @pytest.mark.asyncio
    async def test_delete_users_skip_own_account(self, test_db_session: AsyncSession):
        """Test delete users skips current user"""
        user = Users(
            id="current-user",
            email="current@example.com",
            first_name="Current",
            last_name="User",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user)
        await test_db_session.commit()

        mock_redis = AsyncMock()
        token = {"sub": "current-user"}

        result = await delete_users(test_db_session, mock_redis, ["current-user"], token)

        assert result.failed_count == 1
        assert result.results[0].message == "Cannot delete your own account"

    @pytest.mark.asyncio
    async def test_delete_users_rejects_higher_role_level(self, test_db_session: AsyncSession):
        actor = Users(
            id="actor-del",
            email="actor-del@example.com",
            first_name="Actor",
            last_name="Del",
            phone="+1000000001",
            hash_password="hashed",
            status=True,
            created_at=datetime.now(),
        )
        target = Users(
            id="target-high",
            email="target-high@example.com",
            first_name="Target",
            last_name="High",
            phone="+1000000002",
            hash_password="hashed",
            status=True,
            created_at=datetime.now(),
        )
        actor_role = Roles(id="role-actor", name="manager", description="", level=30)
        target_role = Roles(id="role-target", name="director", description="", level=80)
        test_db_session.add_all([actor, target, actor_role, target_role])
        await test_db_session.commit()
        test_db_session.add_all(
            [
                RoleMapper(user_id=actor.id, role_id=actor_role.id),
                RoleMapper(user_id=target.id, role_id=target_role.id),
            ]
        )
        await test_db_session.commit()

        mock_redis = AsyncMock()
        result = await delete_users(
            test_db_session,
            mock_redis,
            ["target-high"],
            token={"sub": "actor-del"},
        )

        assert result.failed_count == 1
        assert "higher role level" in result.results[0].message


class TestResetUserPassword:
    """Test reset_user_password service function"""

    @pytest.mark.asyncio
    async def test_reset_password_success(self, test_db_session: AsyncSession):
        """Test successful password reset"""
        # Create test user
        user = Users(
            id="user1",
            email="user@example.com",
            first_name="User",
            last_name="Test",
            phone="+1234567890",
            hash_password="old_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user)
        await test_db_session.commit()

        mock_redis = AsyncMock()

        with patch("api.users.services.clear_user_all_sessions") as mock_clear_sessions:
            result = await reset_user_password(
                test_db_session, mock_redis, "user1", "NewPassword123!"
            )

            assert result
            mock_clear_sessions.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_password_user_not_found(self, test_db_session: AsyncSession):
        """Test password reset with non-existent user"""
        mock_redis = AsyncMock()

        with pytest.raises(NotFoundException) as exc_info:
            await reset_user_password(test_db_session, mock_redis, "nonexistent", "NewPassword123!")

        assert "User not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reset_password_server_error(self, test_db_session: AsyncSession):
        """Test password reset server error"""
        user = Users(
            id="user1",
            email="user@example.com",
            first_name="User",
            last_name="Test",
            phone="+1234567890",
            hash_password="old_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user)
        await test_db_session.commit()

        mock_redis = AsyncMock()
        with patch(
            "api.users.services.clear_user_all_sessions", side_effect=Exception("Redis error")
        ):
            with pytest.raises(ServerException):
                await reset_user_password(test_db_session, mock_redis, "user1", "NewPassword123!")


class TestGetUserRoleName:
    """Test _get_user_role_name helper"""

    @pytest.mark.asyncio
    async def test_get_user_role_name_returns_role(self, test_db_session: AsyncSession):
        user = Users(
            id="user1",
            email="user1@example.com",
            first_name="User",
            last_name="One",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        role = Roles(id="role-1", name="user", description="User")
        mapping = RoleMapper(user_id="user1", role_id="role-1")
        test_db_session.add(user)
        test_db_session.add(role)
        test_db_session.add(mapping)
        await test_db_session.commit()

        assert await _get_user_role_name(test_db_session, "user1") == "user"

    @pytest.mark.asyncio
    async def test_get_user_role_name_returns_none_without_role(
        self, test_db_session: AsyncSession
    ):
        assert await _get_user_role_name(test_db_session, "missing") is None


class TestAssertCanManageUserRole:
    """Test role assignment authorization helper"""

    @pytest.mark.asyncio
    async def test_nobody_can_assign_super_admin_role(self, test_db_session: AsyncSession):
        with patch(
            "api.users.services.check_user_has_super_role",
            new_callable=AsyncMock,
            return_value=True,
        ):
            with pytest.raises(AuthorizationException) as exc_info:
                await _assert_can_manage_user_role(
                    test_db_session,
                    "actor1",
                    "super-admin",
                )
            assert "Cannot assign the system super-admin role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cannot_change_role_of_super_admin_user(self, test_db_session: AsyncSession):
        with patch(
            "api.users.services._get_user_role_name",
            new_callable=AsyncMock,
            return_value="super-admin",
        ):
            with pytest.raises(AuthorizationException) as exc_info:
                await _assert_can_manage_user_role(
                    test_db_session,
                    "actor1",
                    "user",
                    target_user_id="super-user",
                )
            assert "Cannot change the role of a system super-admin user" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_super_admin_can_assign_non_system_role(self, test_db_session: AsyncSession):
        with (
            patch(
                "api.users.services.check_user_has_super_role",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "api.users.services._get_user_role_name",
                new_callable=AsyncMock,
                return_value="user",
            ),
        ):
            await _assert_can_manage_user_role(
                test_db_session, "actor1", "user", target_user_id="user1"
            )

    @pytest.mark.asyncio
    async def test_manage_roles_required_for_role_change(self, test_db_session: AsyncSession):
        with (
            patch(
                "api.users.services.check_user_has_super_role",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "api.users.services.get_user_attributes",
                new_callable=AsyncMock,
                return_value={"manage-users": True},
            ),
        ):
            with pytest.raises(AuthorizationException) as exc_info:
                await _assert_can_manage_user_role(test_db_session, "actor1", "user")
            assert "Permission denied to assign roles" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_manage_roles_can_assign_non_super_role(self, test_db_session: AsyncSession):
        with (
            patch(
                "api.users.services.check_user_has_super_role",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "api.users.services.get_user_attributes",
                new_callable=AsyncMock,
                return_value={"manage-roles": True},
            ),
            patch(
                "api.users.services.get_user_role_level",
                new_callable=AsyncMock,
                return_value=50,
            ),
            patch(
                "api.users.services._get_role_level_by_name",
                new_callable=AsyncMock,
                return_value=10,
            ),
        ):
            await _assert_can_manage_user_role(test_db_session, "actor1", "user")

    @pytest.mark.asyncio
    async def test_cannot_assign_higher_role_level(self, test_db_session: AsyncSession):
        with (
            patch(
                "api.users.services.check_user_has_super_role",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "api.users.services.get_user_attributes",
                new_callable=AsyncMock,
                return_value={"manage-roles": True},
            ),
            patch(
                "api.users.services.get_user_role_level",
                new_callable=AsyncMock,
                return_value=20,
            ),
            patch(
                "api.users.services._get_role_level_by_name",
                new_callable=AsyncMock,
                return_value=50,
            ),
        ):
            with pytest.raises(AuthorizationException) as exc_info:
                await _assert_can_manage_user_role(test_db_session, "actor1", "boss")
            assert "higher level" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cannot_manage_user_with_higher_role_level(self, test_db_session: AsyncSession):
        async def fake_level(user_id, _db):
            return 80 if user_id == "target-high" else 20

        with (
            patch(
                "api.users.services.check_user_has_super_role",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "api.users.services.get_user_attributes",
                new_callable=AsyncMock,
                return_value={"manage-roles": True},
            ),
            patch(
                "api.users.services._get_user_role_name",
                new_callable=AsyncMock,
                return_value="manager",
            ),
            patch(
                "api.users.services.get_user_role_level",
                new_callable=AsyncMock,
                side_effect=fake_level,
            ),
            patch(
                "api.users.services._get_role_level_by_name",
                new_callable=AsyncMock,
                return_value=10,
            ),
        ):
            with pytest.raises(AuthorizationException) as exc_info:
                await _assert_can_manage_user_role(
                    test_db_session,
                    "actor1",
                    "user",
                    target_user_id="target-high",
                )
            assert "higher role level" in str(exc_info.value)


class TestUpdateUserOwnRole:
    """Test users cannot change their own role"""

    @pytest.mark.asyncio
    async def test_update_user_rejects_own_role_change(self, test_db_session: AsyncSession):
        user = Users(
            id="self-user",
            email="self@example.com",
            first_name="Self",
            last_name="User",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        test_db_session.add(user)
        await test_db_session.commit()

        with pytest.raises(AuthorizationException) as exc_info:
            await update_user(
                test_db_session,
                "self-user",
                UserUpdate(role="user"),
                actor_user_id="self-user",
            )
        assert "own role" in str(exc_info.value)


class TestRoleManagement:
    """Test role management helper functions"""

    @pytest.mark.asyncio
    async def test_assign_user_role_success(self, test_db_session: AsyncSession):
        """Test successful role assignment"""
        # Create test user and role
        user = Users(
            id="user1",
            email="user@example.com",
            first_name="User",
            last_name="Test",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        role = Roles(id="role1", name="admin", description="Administrator role")
        test_db_session.add(user)
        test_db_session.add(role)
        await test_db_session.commit()

        await _assign_user_role(test_db_session, "user1", "admin")

        # Verify role mapping was created
        result = await test_db_session.execute(
            text("SELECT * FROM role_mapper WHERE user_id = 'user1' AND role_id = 'role1'")
        )
        mapping = result.fetchone()
        assert mapping is not None

    @pytest.mark.asyncio
    async def test_assign_user_role_role_not_found(self, test_db_session: AsyncSession):
        """Test role assignment with non-existent role"""
        with pytest.raises(NotFoundException) as exc_info:
            await _assign_user_role(test_db_session, "user1", "nonexistent_role")

        assert "Role 'nonexistent_role' not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assign_user_role_existing_mapping(self, test_db_session: AsyncSession):
        """Test role assignment skips existing mapping"""
        user = Users(
            id="user1",
            email="user@example.com",
            first_name="User",
            last_name="Test",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        role = Roles(id="role1", name="admin", description="Administrator role")
        test_db_session.add(user)
        test_db_session.add(role)
        await test_db_session.commit()

        test_db_session.add(RoleMapper(user_id="user1", role_id="role1"))
        await test_db_session.commit()

        await _assign_user_role(test_db_session, "user1", "admin")

        result = await test_db_session.execute(
            text("SELECT COUNT(*) FROM role_mapper WHERE user_id = 'user1' AND role_id = 'role1'")
        )
        assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_update_user_role_success(self, test_db_session: AsyncSession):
        """Test successful role update"""
        # Create test user and roles
        user = Users(
            id="user1",
            email="user@example.com",
            first_name="User",
            last_name="Test",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        old_role = Roles(id="role1", name="old_role", description="Old role")
        new_role = Roles(id="role2", name="new_role", description="New role")
        test_db_session.add(user)
        test_db_session.add(old_role)
        test_db_session.add(new_role)
        await test_db_session.commit()

        # Create existing role mapping
        role_mapping = RoleMapper(user_id="user1", role_id="role1")
        test_db_session.add(role_mapping)
        await test_db_session.commit()

        with patch("api.users.services._assign_user_role") as mock_assign_role:
            await _update_user_role(test_db_session, "user1", "new_role")
            mock_assign_role.assert_called_once_with(test_db_session, "user1", "new_role")

    @pytest.mark.asyncio
    async def test_update_user_role_remove_only(self, test_db_session: AsyncSession):
        """Test role update to remove role only"""
        # Create test user and role
        user = Users(
            id="user1",
            email="user@example.com",
            first_name="User",
            last_name="Test",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        role = Roles(id="role1", name="admin", description="Administrator role")
        test_db_session.add(user)
        test_db_session.add(role)
        await test_db_session.commit()

        # Create existing role mapping
        role_mapping = RoleMapper(user_id="user1", role_id="role1")
        test_db_session.add(role_mapping)
        await test_db_session.commit()

        await _update_user_role(test_db_session, "user1", None)

        # Verify role mapping was removed
        result = await test_db_session.execute(
            text("SELECT * FROM role_mapper WHERE user_id = 'user1'")
        )
        mapping = result.fetchone()
        assert mapping is None

    @pytest.mark.asyncio
    async def test_update_user_role_server_error(self, test_db_session: AsyncSession):
        """Test role update server error"""
        with patch.object(test_db_session, "execute", side_effect=Exception("DB error")):
            with pytest.raises(ServerException):
                await _update_user_role(test_db_session, "user1", "admin")

    @pytest.mark.asyncio
    async def test_delete_user_related_records_server_error(self, test_db_session: AsyncSession):
        """Test delete user related records server error"""
        with patch.object(test_db_session, "execute", side_effect=Exception("DB error")):
            with pytest.raises(ServerException):
                await _delete_user_related_records(test_db_session, "user1")

    @pytest.mark.asyncio
    async def test_delete_user_related_records_success(self, test_db_session: AsyncSession):
        user = Users(
            id="user1",
            email="user@example.com",
            first_name="User",
            last_name="Test",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now(),
        )
        role = Roles(id="role1", name="admin", description="Admin")
        expires = datetime.now() + timedelta(hours=1)
        test_db_session.add_all(
            [
                user,
                role,
                LoginLogs(
                    user_id="user1",
                    email="user@example.com",
                    ip_address="127.0.0.1",
                    user_agent="TestAgent/1.0",
                    is_success=True,
                ),
                UserSessions(
                    id="sess-1",
                    user_id="user1",
                    jwt_access_token="token",
                    ip_address="127.0.0.1",
                    user_agent="TestAgent/1.0",
                    is_active=True,
                    expires_at=expires,
                ),
                RoleMapper(user_id="user1", role_id="role1"),
                PasswordResetTokens(
                    user_id="user1",
                    token="reset-token",
                    expires_at=expires,
                ),
                EmailVerificationTokens(
                    user_id="user1",
                    email="user@example.com",
                    token="verify-token",
                    token_type="registration",
                    expires_at=expires,
                ),
            ]
        )
        await test_db_session.commit()

        await _delete_user_related_records(test_db_session, "user1")
        await test_db_session.commit()

        assert (
            await test_db_session.execute(
                text("SELECT COUNT(*) FROM login_logs WHERE user_id = 'user1'")
            )
        ).scalar() == 0
        assert (
            await test_db_session.execute(
                text("SELECT COUNT(*) FROM user_sessions WHERE user_id = 'user1'")
            )
        ).scalar() == 0
        assert (
            await test_db_session.execute(
                text("SELECT COUNT(*) FROM role_mapper WHERE user_id = 'user1'")
            )
        ).scalar() == 0


class TestGetUserRolesMap:
    @pytest.mark.asyncio
    async def test_get_user_roles_map_empty(self, test_db_session: AsyncSession):
        assert await _get_user_roles_map(test_db_session, []) == {}
