import pytest
from datetime import datetime
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.roles import Roles
from models.role_attributes import RoleAttributes
from models.role_attributes_mapper import RoleAttributesMapper
from models.role_mapper import RoleMapper
from models.users import Users
from utils.custom_exception import ConflictException, NotFoundException, ServerException
from api.roles.schema import RoleCreate, RoleUpdate
from api.roles.services import (
    get_all_roles,
    create_role,
    update_role,
    delete_role,
    get_role_attribute_mapping,
    update_role_attribute_mapping,
    check_user_permissions,
)


class TestGetAllRoles:
    """Test get_all_roles service function"""

    @pytest.mark.asyncio
    async def test_get_all_roles_success(self, test_db_session: AsyncSession):
        """Test successful retrieval of all roles"""
        # Create test roles
        role1 = Roles(id="role-1", name="admin", description="Administrator role")
        role2 = Roles(id="role-2", name="user", description="Regular user role")

        test_db_session.add(role1)
        test_db_session.add(role2)
        await test_db_session.commit()

        result = await get_all_roles(test_db_session)

        assert len(result.roles) == 2
        assert result.roles[0].name in ["admin", "user"]
        assert result.roles[1].name in ["admin", "user"]

    @pytest.mark.asyncio
    async def test_get_all_roles_empty(self, test_db_session: AsyncSession):
        """Test get_all_roles when no roles exist"""
        result = await get_all_roles(test_db_session)

        assert len(result.roles) == 0

    @pytest.mark.asyncio
    async def test_get_all_roles_database_error(self, test_db_session: AsyncSession):
        """Test get_all_roles with database error"""
        with patch.object(
            test_db_session, "execute", side_effect=Exception("Database error")
        ):
            with pytest.raises(ServerException) as exc_info:
                await get_all_roles(test_db_session)

            assert "Failed to retrieve roles" in str(exc_info.value)


class TestCreateRole:
    """Test create_role service function"""

    @pytest.mark.asyncio
    async def test_create_role_success(self, test_db_session: AsyncSession):
        """Test successful role creation"""
        role_data = RoleCreate(
            name="manager", description="Manager role with special permissions"
        )

        result = await create_role(test_db_session, role_data)

        assert result.name == "manager"
        assert result.description == "Manager role with special permissions"
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_create_role_minimal_data(self, test_db_session: AsyncSession):
        """Test role creation with minimal data"""
        role_data = RoleCreate(name="guest")

        result = await create_role(test_db_session, role_data)

        assert result.name == "guest"
        assert result.description is None
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_create_role_name_conflict(self, test_db_session: AsyncSession):
        """Test role creation with existing name"""
        # Create existing role
        existing_role = Roles(
            id="existing-role", name="admin", description="Existing admin role"
        )
        test_db_session.add(existing_role)
        await test_db_session.commit()

        role_data = RoleCreate(name="admin", description="New admin role")

        with pytest.raises(ConflictException) as exc_info:
            await create_role(test_db_session, role_data)

        assert "Role name already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_role_database_error(self, test_db_session: AsyncSession):
        """Test create_role with database error"""
        role_data = RoleCreate(name="test-role")

        with patch.object(
            test_db_session, "execute", side_effect=Exception("Database error")
        ):
            with pytest.raises(ServerException) as exc_info:
                await create_role(test_db_session, role_data)

            assert "Failed to create role" in str(exc_info.value)


class TestUpdateRole:
    """Test update_role service function"""

    @pytest.mark.asyncio
    async def test_update_role_success(self, test_db_session: AsyncSession):
        """Test successful role update"""
        # Create test role
        role = Roles(id="role-1", name="admin", description="Original admin role")
        test_db_session.add(role)
        await test_db_session.commit()

        role_data = RoleUpdate(name="updated_admin", description="Updated admin role")

        result = await update_role(test_db_session, "role-1", role_data)

        assert result.name == "updated_admin"
        assert result.description == "Updated admin role"
        assert result.id == "role-1"

    @pytest.mark.asyncio
    async def test_update_role_partial_update(self, test_db_session: AsyncSession):
        """Test partial role update"""
        # Create test role
        role = Roles(id="role-1", name="admin", description="Original admin role")
        test_db_session.add(role)
        await test_db_session.commit()

        role_data = RoleUpdate(name="updated_admin")

        result = await update_role(test_db_session, "role-1", role_data)

        assert result.name == "updated_admin"
        assert result.description == "Original admin role"  # Unchanged
        assert result.id == "role-1"

    @pytest.mark.asyncio
    async def test_update_role_not_found(self, test_db_session: AsyncSession):
        """Test update_role with non-existent role"""
        role_data = RoleUpdate(name="updated_admin")

        with pytest.raises(NotFoundException) as exc_info:
            await update_role(test_db_session, "non-existent-role", role_data)

        assert "Role not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_role_name_conflict(self, test_db_session: AsyncSession):
        """Test update_role with conflicting name"""
        # Create existing roles
        role1 = Roles(id="role-1", name="admin", description="Admin role")
        role2 = Roles(id="role-2", name="user", description="User role")
        test_db_session.add(role1)
        test_db_session.add(role2)
        await test_db_session.commit()

        role_data = RoleUpdate(name="user")  # Try to change admin to user

        with pytest.raises(ConflictException) as exc_info:
            await update_role(test_db_session, "role-1", role_data)

        assert "Role name already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_role_database_error(self, test_db_session: AsyncSession):
        """Test update_role with database error"""
        role_data = RoleUpdate(name="updated_role")

        with patch.object(
            test_db_session, "execute", side_effect=Exception("Database error")
        ):
            with pytest.raises(ServerException) as exc_info:
                await update_role(test_db_session, "role-1", role_data)

            assert "Failed to update role" in str(exc_info.value)


class TestDeleteRole:
    """Test delete_role service function"""

    @pytest.mark.asyncio
    async def test_delete_role_success(self, test_db_session: AsyncSession):
        """Test successful role deletion"""
        # Create test role
        role = Roles(id="role-1", name="admin", description="Admin role")
        test_db_session.add(role)
        await test_db_session.commit()

        result = await delete_role(test_db_session, "role-1")

        assert result is True

        # Verify role is deleted
        deleted_role = await test_db_session.execute(
            select(Roles).where(Roles.id == "role-1")
        )
        assert deleted_role.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_role_not_found(self, test_db_session: AsyncSession):
        """Test delete_role with non-existent role"""
        with pytest.raises(NotFoundException) as exc_info:
            await delete_role(test_db_session, "non-existent-role")

        assert "Role not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_role_assigned_to_users(self, test_db_session: AsyncSession):
        """Test delete_role when role is assigned to users"""
        # Create test user first
        user = Users(
            id="user-1",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            password_reset_required=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Create test role and user mapping
        role = Roles(id="role-1", name="admin", description="Admin role")
        role_mapping = RoleMapper(user_id="user-1", role_id="role-1")

        test_db_session.add(user)
        test_db_session.add(role)
        test_db_session.add(role_mapping)
        await test_db_session.commit()

        with pytest.raises(ConflictException) as exc_info:
            await delete_role(test_db_session, "role-1")

        assert "Cannot delete role that is assigned to users" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_role_database_error(self, test_db_session: AsyncSession):
        """Test delete_role with database error"""
        with patch.object(
            test_db_session, "execute", side_effect=Exception("Database error")
        ):
            with pytest.raises(ServerException) as exc_info:
                await delete_role(test_db_session, "role-1")

            assert "Failed to delete role" in str(exc_info.value)


class TestGetRoleAttributeMapping:
    """Test get_role_attribute_mapping service function"""

    @pytest.mark.asyncio
    async def test_get_role_attribute_mapping_success(
        self, test_db_session: AsyncSession
    ):
        """Test successful role attributes mapping retrieval"""
        # Create test role and attributes
        role = Roles(id="role-1", name="admin", description="Admin role")
        attr1 = RoleAttributes(id="attr-1", name="view-users", description="View users")
        attr2 = RoleAttributes(
            id="attr-2", name="manage-roles", description="Manage roles"
        )
        attr3 = RoleAttributes(
            id="attr-3", name="edit-content", description="Edit content"
        )

        test_db_session.add(role)
        test_db_session.add(attr1)
        test_db_session.add(attr2)
        test_db_session.add(attr3)
        await test_db_session.commit()

        # Create attribute mappings
        mapping1 = RoleAttributesMapper(
            role_id="role-1", attributes_id="attr-1", value=True
        )
        mapping2 = RoleAttributesMapper(
            role_id="role-1", attributes_id="attr-2", value=False
        )

        test_db_session.add(mapping1)
        test_db_session.add(mapping2)
        await test_db_session.commit()

        result = await get_role_attribute_mapping(test_db_session, "role-1")

        assert len(result.attributes) == 3
        assert result.attributes["view-users"] is True
        assert result.attributes["manage-roles"] is False
        assert result.attributes["edit-content"] is False  # No mapping, defaults to False

    @pytest.mark.asyncio
    async def test_get_role_attribute_mapping_role_not_found(
        self, test_db_session: AsyncSession
    ):
        """Test get_role_attribute_mapping with non-existent role"""
        with pytest.raises(NotFoundException) as exc_info:
            await get_role_attribute_mapping(test_db_session, "non-existent-role")

        assert "Role not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_role_attribute_mapping_database_error(
        self, test_db_session: AsyncSession
    ):
        """Test get_role_attribute_mapping with database error"""
        with patch.object(
            test_db_session, "execute", side_effect=Exception("Database error")
        ):
            with pytest.raises(ServerException) as exc_info:
                await get_role_attribute_mapping(test_db_session, "role-1")

            assert "Failed to get role attributes" in str(exc_info.value)


class TestUpdateRoleAttributeMapping:
    """Test update_role_attribute_mapping service function"""

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_success(
        self, test_db_session: AsyncSession
    ):
        """Test successful role attributes mapping update"""
        # Create test role and attributes
        role = Roles(id="role-1", name="admin", description="Admin role")
        attr1 = RoleAttributes(id="attr-1", name="view-users", description="View users")
        attr2 = RoleAttributes(
            id="attr-2", name="manage-roles", description="Manage roles"
        )

        test_db_session.add(role)
        test_db_session.add(attr1)
        test_db_session.add(attr2)
        await test_db_session.commit()

        attributes_data = {"view-users": True, "manage-roles": False}

        result = await update_role_attribute_mapping(
            test_db_session, "role-1", attributes_data
        )

        assert result.total_attributes == 2
        assert result.success_count == 2
        assert result.failed_count == 0
        assert len(result.results) == 2

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_partial_success(
        self, test_db_session: AsyncSession
    ):
        """Test role attributes mapping update with partial success"""
        # Create test role and valid attribute
        role = Roles(id="role-1", name="admin", description="Admin role")
        attr1 = RoleAttributes(id="attr-1", name="view-users", description="View users")

        test_db_session.add(role)
        test_db_session.add(attr1)
        await test_db_session.commit()

        attributes_data = {
            "view-users": True,
            "invalid-attr-name": False,  # Invalid attribute name
        }

        result = await update_role_attribute_mapping(
            test_db_session, "role-1", attributes_data
        )

        assert result.total_attributes == 2
        assert result.success_count == 1
        assert result.failed_count == 1
        assert len(result.results) == 2

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_role_not_found(
        self, test_db_session: AsyncSession
    ):
        """Test update_role_attribute_mapping with non-existent role"""
        attributes_data = {"view-users": True}

        with pytest.raises(NotFoundException) as exc_info:
            await update_role_attribute_mapping(
                test_db_session, "non-existent-role", attributes_data
            )

        assert "Role not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_database_error(
        self, test_db_session: AsyncSession
    ):
        """Test update_role_attribute_mapping with database error"""
        attributes_data = {"view-users": True}

        with patch.object(
            test_db_session, "execute", side_effect=Exception("Database error")
        ):
            with pytest.raises(ServerException) as exc_info:
                await update_role_attribute_mapping(
                    test_db_session, "role-1", attributes_data
                )

            assert "Failed to update role attributes mapping" in str(exc_info.value)


class TestCheckUserPermissions:
    """Test check_user_permissions service function"""

    @pytest.mark.asyncio
    async def test_check_user_permissions_success(self, test_db_session: AsyncSession):
        """Test successful user permissions check"""
        # Create test user first
        user = Users(
            id="user-1",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            phone="+1234567890",
            hash_password="hashed_password",
            status=True,
            password_reset_required=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Create test role, attributes and mappings
        # Use a different role name to avoid super admin check
        role = Roles(id="role-1", name="test-role", description="Test role")
        attr1 = RoleAttributes(id="attr-1", name="view-users", description="View users")
        attr2 = RoleAttributes(
            id="attr-2", name="manage-roles", description="Manage roles"
        )
        attr3 = RoleAttributes(
            id="attr-3", name="edit-content", description="Edit content"
        )

        role_mapping = RoleMapper(user_id="user-1", role_id="role-1")
        attr_mapping1 = RoleAttributesMapper(
            role_id="role-1", attributes_id="attr-1", value=True
        )
        attr_mapping2 = RoleAttributesMapper(
            role_id="role-1", attributes_id="attr-2", value=False
        )

        test_db_session.add(user)
        test_db_session.add(role)
        test_db_session.add(attr1)
        test_db_session.add(attr2)
        test_db_session.add(attr3)
        test_db_session.add(role_mapping)
        test_db_session.add(attr_mapping1)
        test_db_session.add(attr_mapping2)
        await test_db_session.commit()

        required_attributes = ["view-users", "manage-roles", "edit-content"]

        result = await check_user_permissions(
            test_db_session, "user-1", required_attributes
        )

        assert result.permissions["view-users"] is True
        assert result.permissions["manage-roles"] is False
        assert result.permissions["edit-content"] is False

    @pytest.mark.asyncio
    async def test_check_user_permissions_no_role(self, test_db_session: AsyncSession):
        """Test user permissions check when user has no role"""
        required_attributes = ["view-users", "manage-roles"]

        result = await check_user_permissions(
            test_db_session, "user-without-role", required_attributes
        )

        assert result.permissions["view-users"] is False
        assert result.permissions["manage-roles"] is False

    @pytest.mark.asyncio
    async def test_check_user_permissions_database_error(
        self, test_db_session: AsyncSession
    ):
        """Test check_user_permissions with database error"""
        required_attributes = ["view-users"]

        with patch.object(
            test_db_session, "execute", side_effect=Exception("Database error")
        ):
            with pytest.raises(ServerException) as exc_info:
                await check_user_permissions(
                    test_db_session, "user-1", required_attributes
                )

            assert "Failed to check user permissions" in str(exc_info.value)