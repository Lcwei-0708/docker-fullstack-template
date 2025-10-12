import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import Users
from models.roles import Roles
from models.role_mapper import RoleMapper
from utils.custom_exception import ConflictException, NotFoundException
from api.users.services import (
    get_all_users,
    create_user,
    update_user,
    delete_users,
    reset_user_password,
    _assign_user_role,
    _update_user_role,
)
from api.users.schema import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserPagination,
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
            created_at=datetime.now()
        )
        user2 = Users(
            id="user2",
            email="user2@example.com",
            first_name="User",
            last_name="Two",
            phone="+1234567891",
            hash_password="hashed_password",
            status=False,
            created_at=datetime.now()
        )
        
        test_db_session.add(user1)
        test_db_session.add(user2)
        await test_db_session.commit()

        result = await get_all_users(
            db=test_db_session,
            page=1,
            per_page=10
        )

        assert isinstance(result, UserPagination)
        assert result.total == 2
        assert len(result.users) == 2
        assert result.page == 1
        assert result.per_page == 10

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
            created_at=datetime.now()
        )
        user2 = Users(
            id="user2",
            email="jane.smith@example.com",
            first_name="Jane",
            last_name="Smith",
            phone="+1234567891",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now()
        )
        
        test_db_session.add(user1)
        test_db_session.add(user2)
        await test_db_session.commit()

        result = await get_all_users(
            db=test_db_session,
            keyword="john",
            page=1,
            per_page=10
        )

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
            created_at=datetime.now()
        )
        user2 = Users(
            id="user2",
            email="inactive@example.com",
            first_name="Inactive",
            last_name="User",
            phone="+1234567891",
            hash_password="hashed_password",
            status=False,
            created_at=datetime.now()
        )
        
        test_db_session.add(user1)
        test_db_session.add(user2)
        await test_db_session.commit()

        result = await get_all_users(
            db=test_db_session,
            status="true",
            page=1,
            per_page=10
        )

        assert result.total == 1
        assert len(result.users) == 1
        assert result.users[0].status == True

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
            created_at=datetime.now()
        )
        test_db_session.add(user)
        await test_db_session.commit()

        # Create test role
        role = Roles(
            id="role1",
            name="admin",
            description="Administrator role"
        )
        test_db_session.add(role)
        await test_db_session.commit()

        # Create role mapping
        role_mapping = RoleMapper(
            user_id="user1",
            role_id="role1"
        )
        test_db_session.add(role_mapping)
        await test_db_session.commit()

        result = await get_all_users(
            db=test_db_session,
            role="admin",
            page=1,
            per_page=10
        )

        assert result.total == 1
        assert len(result.users) == 1
        assert result.users[0].role == "admin"

    @pytest.mark.asyncio
    async def test_get_all_users_empty_result(self, test_db_session: AsyncSession):
        """Test users retrieval with no results"""
        result = await get_all_users(
            db=test_db_session,
            page=1,
            per_page=10
        )

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
                created_at=datetime.now()
            )
            test_db_session.add(user)
        
        await test_db_session.commit()

        result = await get_all_users(
            db=test_db_session,
            page=2,
            per_page=10
        )

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
            created_at=datetime.now()
        )
        user2 = Users(
            id="user2",
            email="b@example.com",
            first_name="B",
            last_name="User",
            phone="+1234567891",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now()
        )
        
        test_db_session.add(user1)
        test_db_session.add(user2)
        await test_db_session.commit()

        result = await get_all_users(
            db=test_db_session,
            sort_by="email",
            desc=False,
            page=1,
            per_page=10
        )

        assert len(result.users) == 2
        assert result.users[0].email == "a@example.com"
        assert result.users[1].email == "b@example.com"


class TestCreateUser:
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
            role="admin"
        )

        with patch("api.users.services._assign_user_role") as mock_assign_role:
            result = await create_user(test_db_session, user_data)

            assert isinstance(result, UserResponse)
            assert result.email == user_data.email
            assert result.first_name == user_data.first_name
            assert result.last_name == user_data.last_name
            assert result.phone == user_data.phone
            assert result.status == user_data.status
            assert result.role == user_data.role

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
            created_at=datetime.now()
        )
        test_db_session.add(existing_user)
        await test_db_session.commit()

        user_data = UserCreate(
            first_name="John",
            last_name="Doe",
            email="existing@example.com",
            phone="+1234567890",
            password="TestPassword123!",
            status=True
        )

        with pytest.raises(ConflictException) as exc_info:
            await create_user(test_db_session, user_data)
        
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
            status=True
        )

        result = await create_user(test_db_session, user_data)

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
            created_at=datetime.now()
        )
        test_db_session.add(user)
        await test_db_session.commit()

        update_data = UserUpdate(
            first_name="Updated",
            last_name="Name",
            email="updated@example.com"
        )

        with patch("api.users.services._update_user_role") as mock_update_role:
            result = await update_user(test_db_session, "user1", update_data)

            assert isinstance(result, UserResponse)
            assert result.first_name == "Updated"
            assert result.last_name == "Name"
            assert result.email == "updated@example.com"

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, test_db_session: AsyncSession):
        """Test user update with non-existent user"""
        update_data = UserUpdate(first_name="Updated")

        with pytest.raises(NotFoundException) as exc_info:
            await update_user(test_db_session, "nonexistent", update_data)
        
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
            created_at=datetime.now()
        )
        user2 = Users(
            id="user2",
            email="user2@example.com",
            first_name="User",
            last_name="Two",
            phone="+1234567891",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now()
        )
        test_db_session.add(user1)
        test_db_session.add(user2)
        await test_db_session.commit()

        update_data = UserUpdate(email="user2@example.com")

        with pytest.raises(ConflictException) as exc_info:
            await update_user(test_db_session, "user1", update_data)
        
        assert "Email already exists" in str(exc_info.value)


class TestDeleteUsers:
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
            created_at=datetime.now()
        )
        user2 = Users(
            id="user2",
            email="user2@example.com",
            first_name="User",
            last_name="Two",
            phone="+1234567891",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now()
        )
        test_db_session.add(user1)
        test_db_session.add(user2)
        await test_db_session.commit()

        result = await delete_users(test_db_session, ["user1", "user2"])

        assert result == True

    @pytest.mark.asyncio
    async def test_delete_users_not_found(self, test_db_session: AsyncSession):
        """Test users deletion with non-existent users"""
        with pytest.raises(NotFoundException) as exc_info:
            await delete_users(test_db_session, ["nonexistent1", "nonexistent2"])
        
        assert "Users not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_users_partial_not_found(self, test_db_session: AsyncSession):
        """Test users deletion with some non-existent users"""
        # Create one user
        user = Users(
            id="user1",
            email="user1@example.com",
            first_name="User",
            last_name="One",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            created_at=datetime.now()
        )
        test_db_session.add(user)
        await test_db_session.commit()

        with pytest.raises(NotFoundException) as exc_info:
            await delete_users(test_db_session, ["user1", "nonexistent"])
        
        assert "Users not found" in str(exc_info.value)


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
            created_at=datetime.now()
        )
        test_db_session.add(user)
        await test_db_session.commit()

        mock_redis = AsyncMock()
        
        with patch("api.users.services.clear_user_all_sessions") as mock_clear_sessions:
            result = await reset_user_password(
                test_db_session, 
                mock_redis, 
                "user1", 
                "NewPassword123!"
            )

            assert result == True
            mock_clear_sessions.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_password_user_not_found(self, test_db_session: AsyncSession):
        """Test password reset with non-existent user"""
        mock_redis = AsyncMock()

        with pytest.raises(NotFoundException) as exc_info:
            await reset_user_password(
                test_db_session, 
                mock_redis, 
                "nonexistent", 
                "NewPassword123!"
            )
        
        assert "User not found" in str(exc_info.value)


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
            created_at=datetime.now()
        )
        role = Roles(
            id="role1",
            name="admin",
            description="Administrator role"
        )
        test_db_session.add(user)
        test_db_session.add(role)
        await test_db_session.commit()

        await _assign_user_role(test_db_session, "user1", "admin")

        # Verify role mapping was created
        from sqlalchemy import text
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
            created_at=datetime.now()
        )
        old_role = Roles(
            id="role1",
            name="old_role",
            description="Old role"
        )
        new_role = Roles(
            id="role2",
            name="new_role",
            description="New role"
        )
        test_db_session.add(user)
        test_db_session.add(old_role)
        test_db_session.add(new_role)
        await test_db_session.commit()

        # Create existing role mapping
        role_mapping = RoleMapper(
            user_id="user1",
            role_id="role1"
        )
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
            created_at=datetime.now()
        )
        role = Roles(
            id="role1",
            name="admin",
            description="Administrator role"
        )
        test_db_session.add(user)
        test_db_session.add(role)
        await test_db_session.commit()

        # Create existing role mapping
        role_mapping = RoleMapper(
            user_id="user1",
            role_id="role1"
        )
        test_db_session.add(role_mapping)
        await test_db_session.commit()

        await _update_user_role(test_db_session, "user1", None)

        # Verify role mapping was removed
        result = await test_db_session.execute(
            text("SELECT * FROM role_mapper WHERE user_id = 'user1'")
        )
        mapping = result.fetchone()
        assert mapping is None