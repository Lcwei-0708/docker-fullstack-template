from datetime import datetime
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.roles.schema import RoleCreate, RoleUpdate
from api.roles.services import (
    check_user_permissions,
    create_role,
    delete_role,
    get_all_roles,
    get_role_attribute_mapping,
    update_role,
    update_role_attribute_mapping,
)
from models.role_attributes import RoleAttributes
from models.role_attributes_mapper import RoleAttributesMapper
from models.role_mapper import RoleMapper
from models.roles import Roles
from models.users import Users
from utils.custom_exception import (
    AuthorizationException,
    ConflictException,
    NotFoundException,
    ServerException,
)


async def _create_actor(
    db: AsyncSession,
    *,
    level: int = 100,
    user_id: str = "actor-1",
    role_name: str | None = None,
) -> str:
    """Seed an actor user with a role level for hierarchy checks."""
    role = Roles(
        id=f"actor-role-{user_id}",
        name=role_name or f"actor-role-{user_id}",
        description="Actor role",
        level=level,
    )
    user = Users(
        id=user_id,
        email=f"{user_id}@example.com",
        first_name="Actor",
        last_name="User",
        phone="0000000000",
        hash_password="hashed",
        status=True,
    )
    db.add_all([role, user])
    await db.commit()
    db.add(RoleMapper(user_id=user.id, role_id=role.id))
    await db.commit()
    return user_id


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

        actor = await _create_actor(test_db_session, role_name="super-admin")
        result = await get_all_roles(test_db_session, actor_user_id=actor)

        assert len(result.roles) == 2
        assert result.roles[0].name in ["admin", "user"]
        assert result.roles[1].name in ["admin", "user"]
        assert result.actor_level == 100
        assert result.actor_role_id == f"actor-role-{actor}"

    @pytest.mark.asyncio
    async def test_get_all_roles_empty(self, test_db_session: AsyncSession):
        """Test get_all_roles when no roles exist"""
        actor = await _create_actor(test_db_session, role_name="super-admin")
        result = await get_all_roles(test_db_session, actor_user_id=actor)

        assert len(result.roles) == 0
        assert result.actor_level == 100
        assert result.actor_role_id == f"actor-role-{actor}"

    @pytest.mark.asyncio
    async def test_get_all_roles_database_error(self, test_db_session: AsyncSession):
        """Test get_all_roles with database error"""
        with patch.object(test_db_session, "execute", side_effect=Exception("Database error")):
            with pytest.raises(ServerException) as exc_info:
                await get_all_roles(test_db_session, actor_user_id="actor-1")

            assert "Failed to retrieve roles" in str(exc_info.value)


class TestCreateRole:
    """Test create_role service function"""

    @pytest.mark.asyncio
    async def test_create_role_success(self, test_db_session: AsyncSession):
        """Test successful role creation"""
        role_data = RoleCreate(
            name="manager",
            description="Manager role with special permissions",
            level=10,
        )

        actor = await _create_actor(test_db_session)

        result = await create_role(test_db_session, role_data, actor_user_id=actor)

        assert result.name == "manager"
        assert result.description == "Manager role with special permissions"
        assert result.level == 10
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_create_role_rejects_level_too_high(self, test_db_session: AsyncSession):
        """Test role creation rejects level > actor level"""
        actor = await _create_actor(test_db_session, level=20, user_id="actor-low")
        role_data = RoleCreate(name="too-high", description="blocked", level=21)

        with pytest.raises(AuthorizationException) as exc_info:
            await create_role(test_db_session, role_data, actor_user_id=actor)

        assert "higher than your own" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_role_allows_same_level(self, test_db_session: AsyncSession):
        """Test role creation allows level equal to actor level"""
        actor = await _create_actor(test_db_session, level=20, user_id="actor-same")
        role_data = RoleCreate(name="peer-role", description="same level", level=20)

        result = await create_role(test_db_session, role_data, actor_user_id=actor)

        assert result.name == "peer-role"
        assert result.level == 20

    @pytest.mark.asyncio
    async def test_create_role_minimal_data(self, test_db_session: AsyncSession):
        """Test role creation with minimal data"""
        role_data = RoleCreate(
            name="guest",
            level=10,
        )

        actor = await _create_actor(test_db_session)

        result = await create_role(test_db_session, role_data, actor_user_id=actor)

        assert result.name == "guest"
        assert result.description is None
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_create_role_name_conflict(self, test_db_session: AsyncSession):
        """Test role creation with existing name"""
        # Create existing role
        existing_role = Roles(id="existing-role", name="admin", description="Existing admin role")
        test_db_session.add(existing_role)
        await test_db_session.commit()

        role_data = RoleCreate(
            name="admin",
            description="New admin role",
            level=10,
        )

        with pytest.raises(ConflictException) as exc_info:
            actor = await _create_actor(test_db_session)
            await create_role(test_db_session, role_data, actor_user_id=actor)

        assert "Role name already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_role_database_error(self, test_db_session: AsyncSession):
        """Test create_role with database error"""
        role_data = RoleCreate(
            name="test-role",
            level=10,
        )

        actor = await _create_actor(test_db_session)
        with patch.object(test_db_session, "commit", side_effect=Exception("Database error")):
            with pytest.raises(ServerException) as exc_info:
                await create_role(test_db_session, role_data, actor_user_id=actor)

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

        actor = await _create_actor(test_db_session)
        result = await update_role(test_db_session, "role-1", role_data, actor_user_id=actor)

        assert result.name == "updated_admin"
        assert result.description == "Updated admin role"
        assert result.id == "role-1"

    @pytest.mark.asyncio
    async def test_update_role_rejects_own_role(self, test_db_session: AsyncSession):
        """Test update_role blocks modifying the actor's own role"""
        actor = await _create_actor(test_db_session, user_id="actor-own-update", level=50)
        role_data = RoleUpdate(description="self demotion attempt")

        with pytest.raises(AuthorizationException) as exc_info:
            await update_role(
                test_db_session,
                f"actor-role-{actor}",
                role_data,
                actor_user_id=actor,
            )

        assert "own role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_role_partial_update(self, test_db_session: AsyncSession):
        """Test partial role update"""
        # Create test role
        role = Roles(id="role-1", name="admin", description="Original admin role")
        test_db_session.add(role)
        await test_db_session.commit()

        role_data = RoleUpdate(name="updated_admin")

        actor = await _create_actor(test_db_session)
        result = await update_role(test_db_session, "role-1", role_data, actor_user_id=actor)

        assert result.name == "updated_admin"
        assert result.description == "Original admin role"  # Unchanged
        assert result.id == "role-1"

    @pytest.mark.asyncio
    async def test_update_role_not_found(self, test_db_session: AsyncSession):
        """Test update_role with non-existent role"""
        role_data = RoleUpdate(name="updated_admin")

        with pytest.raises(NotFoundException) as exc_info:
            actor = await _create_actor(test_db_session)
            await update_role(test_db_session, "non-existent-role", role_data, actor_user_id=actor)

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
            actor = await _create_actor(test_db_session)
            await update_role(test_db_session, "role-1", role_data, actor_user_id=actor)

        assert "Role name already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_role_database_error(self, test_db_session: AsyncSession):
        """Test update_role with database error"""
        role = Roles(id="role-1", name="admin", description="Admin role")
        test_db_session.add(role)
        await test_db_session.commit()

        actor = await _create_actor(test_db_session)
        role_data = RoleUpdate(name="updated_role")

        with patch.object(test_db_session, "execute", side_effect=Exception("Database error")):
            with pytest.raises(ServerException) as exc_info:
                await update_role(test_db_session, "role-1", role_data, actor_user_id=actor)

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

        actor = await _create_actor(test_db_session)
        result = await delete_role(test_db_session, "role-1", actor_user_id=actor)

        assert result is True

        # Verify role is deleted
        deleted_role = await test_db_session.execute(select(Roles).where(Roles.id == "role-1"))
        assert deleted_role.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_role_rejects_own_role(self, test_db_session: AsyncSession):
        """Test delete_role blocks deleting the actor's own role"""
        actor = await _create_actor(test_db_session, user_id="actor-own-delete", level=50)

        with pytest.raises(AuthorizationException) as exc_info:
            await delete_role(
                test_db_session,
                f"actor-role-{actor}",
                actor_user_id=actor,
            )

        assert "own role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_role_not_found(self, test_db_session: AsyncSession):
        """Test delete_role with non-existent role"""
        with pytest.raises(NotFoundException) as exc_info:
            actor = await _create_actor(test_db_session)
            await delete_role(test_db_session, "non-existent-role", actor_user_id=actor)

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
            actor = await _create_actor(test_db_session)
            await delete_role(test_db_session, "role-1", actor_user_id=actor)

        assert "Cannot delete role that is assigned to users" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_role_database_error(self, test_db_session: AsyncSession):
        """Test delete_role with database error"""
        role = Roles(id="role-1", name="admin", description="Admin role")
        test_db_session.add(role)
        await test_db_session.commit()

        actor = await _create_actor(test_db_session)

        with patch.object(test_db_session, "execute", side_effect=Exception("Database error")):
            with pytest.raises(ServerException) as exc_info:
                await delete_role(test_db_session, "role-1", actor_user_id=actor)

            assert "Failed to delete role" in str(exc_info.value)


class TestGetRoleAttributeMapping:
    """Test get_role_attribute_mapping service function"""

    @pytest.mark.asyncio
    async def test_get_role_attribute_mapping_success(self, test_db_session: AsyncSession):
        """Test successful role attributes mapping retrieval"""
        # Create test role and attributes
        role = Roles(id="role-1", name="admin", description="Admin role")
        attr1 = RoleAttributes(
            id="attr-1", name="view-users", group="user-role-management", category="user"
        )
        attr2 = RoleAttributes(
            id="attr-2", name="manage-roles", group="user-role-management", category="role"
        )
        attr3 = RoleAttributes(id="attr-3", name="edit-content", group=None, category=None)

        test_db_session.add(role)
        test_db_session.add(attr1)
        test_db_session.add(attr2)
        test_db_session.add(attr3)
        await test_db_session.commit()

        # Create attribute mappings
        mapping1 = RoleAttributesMapper(role_id="role-1", attributes_id="attr-1", value=True)
        mapping2 = RoleAttributesMapper(role_id="role-1", attributes_id="attr-2", value=False)

        test_db_session.add(mapping1)
        test_db_session.add(mapping2)
        await test_db_session.commit()

        result = await get_role_attribute_mapping(test_db_session, "role-1")

        groups = {
            g.group: {cat: {a.name: a for a in attrs} for cat, attrs in g.categories.items()}
            for g in result.groups
        }
        assert set(groups.keys()) == {"default", "user-role-management"}

        assert groups["user-role-management"]["user"]["view-users"].value is True

        assert groups["user-role-management"]["role"]["manage-roles"].value is False

        # No mapping, defaults to False; and both group/category missing -> default/uncategorized
        assert groups["default"]["uncategorized"]["edit-content"].value is False

    @pytest.mark.asyncio
    async def test_get_role_attribute_mapping_role_not_found(self, test_db_session: AsyncSession):
        """Test get_role_attribute_mapping with non-existent role"""
        with pytest.raises(NotFoundException) as exc_info:
            await get_role_attribute_mapping(test_db_session, "non-existent-role")

        assert "Role not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_role_attribute_mapping_database_error(self, test_db_session: AsyncSession):
        """Test get_role_attribute_mapping with database error"""
        with patch.object(test_db_session, "execute", side_effect=Exception("Database error")):
            with pytest.raises(ServerException) as exc_info:
                await get_role_attribute_mapping(test_db_session, "role-1")

            assert "Failed to get role attributes" in str(exc_info.value)


class TestUpdateRoleAttributeMapping:
    """Test update_role_attribute_mapping service function"""

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_success(self, test_db_session: AsyncSession):
        """Test successful role attributes mapping update"""
        # Create test role and attributes
        role = Roles(id="role-1", name="admin", description="Admin role")
        attr1 = RoleAttributes(id="attr-1", name="view-users")
        attr2 = RoleAttributes(id="attr-2", name="manage-roles")

        test_db_session.add(role)
        test_db_session.add(attr1)
        test_db_session.add(attr2)
        await test_db_session.commit()

        attributes_data = {"view-users": True, "manage-roles": False}

        result = await update_role_attribute_mapping(
            test_db_session,
            "role-1",
            attributes_data,
            actor_user_id=await _create_actor(test_db_session),
        )

        assert result.total_attributes == 2
        assert result.success_count == 2
        assert result.failed_count == 0
        assert len(result.results) == 2

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_rejects_own_role(
        self, test_db_session: AsyncSession
    ):
        """Test update_role_attribute_mapping blocks changing own role permissions"""
        actor = await _create_actor(test_db_session, user_id="actor-own-attrs", level=50)
        attr = RoleAttributes(id="attr-own", name="view-users")
        test_db_session.add(attr)
        await test_db_session.commit()

        with pytest.raises(AuthorizationException) as exc_info:
            await update_role_attribute_mapping(
                test_db_session,
                f"actor-role-{actor}",
                {"view-users": False},
                actor_user_id=actor,
            )

        assert "own role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_partial_success(
        self, test_db_session: AsyncSession
    ):
        """Test role attributes mapping update with partial success"""
        # Create test role and valid attribute
        role = Roles(id="role-1", name="admin", description="Admin role")
        attr1 = RoleAttributes(id="attr-1", name="view-users")

        test_db_session.add(role)
        test_db_session.add(attr1)
        await test_db_session.commit()

        attributes_data = {
            "view-users": True,
            "invalid-attr-name": False,  # Invalid attribute name
        }

        result = await update_role_attribute_mapping(
            test_db_session,
            "role-1",
            attributes_data,
            actor_user_id=await _create_actor(test_db_session),
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
                test_db_session,
                "non-existent-role",
                attributes_data,
                actor_user_id=await _create_actor(test_db_session),
            )

        assert "Role not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_role_attribute_mapping_database_error(
        self, test_db_session: AsyncSession
    ):
        """Test update_role_attribute_mapping with database error"""
        attributes_data = {"view-users": True}
        actor = await _create_actor(test_db_session)

        with patch.object(test_db_session, "execute", side_effect=Exception("Database error")):
            with pytest.raises(ServerException) as exc_info:
                await update_role_attribute_mapping(
                    test_db_session,
                    "role-1",
                    attributes_data,
                    actor_user_id=actor,
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
        # Use a different role name to avoid system super-admin protection
        role = Roles(id="role-1", name="test-role", description="Test role")
        attr1 = RoleAttributes(id="attr-1", name="view-users")
        attr2 = RoleAttributes(id="attr-2", name="manage-roles")
        attr3 = RoleAttributes(id="attr-3", name="edit-content")

        role_mapping = RoleMapper(user_id="user-1", role_id="role-1")
        attr_mapping1 = RoleAttributesMapper(role_id="role-1", attributes_id="attr-1", value=True)
        attr_mapping2 = RoleAttributesMapper(role_id="role-1", attributes_id="attr-2", value=False)

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

        result = await check_user_permissions(test_db_session, "user-1", required_attributes)

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
    async def test_check_user_permissions_database_error(self, test_db_session: AsyncSession):
        """Test check_user_permissions with database error"""
        required_attributes = ["view-users"]

        with patch.object(test_db_session, "execute", side_effect=Exception("Database error")):
            with pytest.raises(ServerException) as exc_info:
                await check_user_permissions(test_db_session, "user-1", required_attributes)

            assert "Failed to check user permissions" in str(exc_info.value)


class TestSuperAdminRoleProtection:
    """Test system super-admin role cannot be listed or mutated via roles API"""

    @pytest.mark.asyncio
    async def test_get_all_roles_excludes_super_admin(self, test_db_session: AsyncSession):
        super_role = Roles(
            id="role-super", name="super-admin", description="System super-admin", level=100
        )
        user_role = Roles(id="role-user", name="user", description="User role", level=1)
        actor_user = Users(
            id="actor-super",
            email="actor-super@example.com",
            first_name="Actor",
            last_name="Super",
            phone="0000000000",
            hash_password="hashed",
            status=True,
        )
        test_db_session.add_all([super_role, user_role, actor_user])
        await test_db_session.commit()
        test_db_session.add(RoleMapper(user_id=actor_user.id, role_id=super_role.id))
        await test_db_session.commit()

        result = await get_all_roles(test_db_session, actor_user_id=actor_user.id)

        names = [role.name for role in result.roles]
        assert names == ["user"]
        assert "super-admin" not in names
        assert result.actor_level == 100
        assert result.actor_role_id == "role-super"

    @pytest.mark.asyncio
    async def test_create_role_rejects_super_admin_name(self, test_db_session: AsyncSession):
        with pytest.raises(AuthorizationException) as exc_info:
            await create_role(
                test_db_session,
                RoleCreate(
                    name="super-admin",
                    description="blocked",
                    level=10,
                ),
                actor_user_id=await _create_actor(test_db_session),
            )
        assert "Cannot create the system super-admin role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_role_rejects_mutating_super_admin(self, test_db_session: AsyncSession):
        role = Roles(id="role-super", name="super-admin", description="System super-admin")
        test_db_session.add(role)
        await test_db_session.commit()

        with pytest.raises(AuthorizationException) as exc_info:
            await update_role(
                test_db_session,
                "role-super",
                RoleUpdate(description="should fail"),
                actor_user_id=await _create_actor(test_db_session),
            )
        assert "Cannot modify the system super-admin role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_role_rejects_rename_to_super_admin(self, test_db_session: AsyncSession):
        role = Roles(id="role-1", name="manager", description="Manager")
        test_db_session.add(role)
        await test_db_session.commit()

        with pytest.raises(AuthorizationException) as exc_info:
            await update_role(
                test_db_session,
                "role-1",
                RoleUpdate(name="super-admin"),
                actor_user_id=await _create_actor(test_db_session),
            )
        assert "Cannot rename a role to the system super-admin role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_role_rejects_super_admin(self, test_db_session: AsyncSession):
        role = Roles(id="role-super", name="super-admin", description="System super-admin")
        test_db_session.add(role)
        await test_db_session.commit()

        with pytest.raises(AuthorizationException) as exc_info:
            actor = await _create_actor(test_db_session)
            await delete_role(test_db_session, "role-super", actor_user_id=actor)
        assert "Cannot modify the system super-admin role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_role_attributes_rejects_super_admin(self, test_db_session: AsyncSession):
        role = Roles(id="role-super", name="super-admin", description="System super-admin")
        test_db_session.add(role)
        await test_db_session.commit()

        with pytest.raises(AuthorizationException) as exc_info:
            await get_role_attribute_mapping(test_db_session, "role-super")
        assert "Cannot modify the system super-admin role" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_role_attributes_rejects_super_admin(self, test_db_session: AsyncSession):
        role = Roles(id="role-super", name="super-admin", description="System super-admin")
        test_db_session.add(role)
        await test_db_session.commit()

        with pytest.raises(AuthorizationException) as exc_info:
            await update_role_attribute_mapping(
                test_db_session,
                "role-super",
                {"view-users": True},
                actor_user_id=await _create_actor(test_db_session),
            )
        assert "Cannot modify the system super-admin role" in str(exc_info.value)
