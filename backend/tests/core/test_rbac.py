from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7

from core.config import settings
from core.permissions import Permission
from core.rbac import (
    check_user_has_super_role,
    get_user_attributes,
    is_super_admin_role_name,
    require_permission,
)
from models.role_attributes import RoleAttributes
from models.role_attributes_mapper import RoleAttributesMapper
from models.role_mapper import RoleMapper
from models.roles import Roles
from models.users import Users
from utils.custom_exception import ServerException


class TestIsSuperAdminRoleName:
    def test_matches_configured_name(self):
        assert is_super_admin_role_name(settings.DEFAULT_SUPER_ADMIN_ROLE) is True

    def test_rejects_other_or_empty(self):
        assert is_super_admin_role_name("admin") is False
        assert is_super_admin_role_name("") is False
        assert is_super_admin_role_name(None) is False


class TestCheckUserHasSuperRole:
    @pytest.mark.asyncio
    async def test_returns_true_for_super_admin(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        role = Roles(
            id=str(uuid7()),
            name=settings.DEFAULT_SUPER_ADMIN_ROLE,
            description="super",
        )
        test_db_session.add(role)
        await test_db_session.commit()
        test_db_session.add(RoleMapper(user_id=test_user.id, role_id=role.id))
        await test_db_session.commit()

        assert await check_user_has_super_role(test_user.id, test_db_session) is True

    @pytest.mark.asyncio
    async def test_returns_false_without_role(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        assert await check_user_has_super_role(test_user.id, test_db_session) is False

    @pytest.mark.asyncio
    async def test_raises_server_exception_on_error(self):
        db = AsyncMock()
        db.execute.side_effect = RuntimeError("db down")
        with pytest.raises(ServerException, match="Failed to check super role"):
            await check_user_has_super_role("user-1", db)


class TestGetUserAttributes:
    @pytest.mark.asyncio
    async def test_super_admin_gets_all_attributes(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        role = Roles(
            id=str(uuid7()),
            name=settings.DEFAULT_SUPER_ADMIN_ROLE,
            description="super",
        )
        attr = RoleAttributes(id=str(uuid7()), name="view-users")
        test_db_session.add_all([role, attr])
        await test_db_session.commit()
        test_db_session.add(RoleMapper(user_id=test_user.id, role_id=role.id))
        await test_db_session.commit()

        attributes = await get_user_attributes(test_user.id, test_db_session)
        assert attributes == {"view-users": True}

    @pytest.mark.asyncio
    async def test_merges_attribute_values_with_or(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        role_true = Roles(id=str(uuid7()), name="role-true", description="t")
        role_false = Roles(id=str(uuid7()), name="role-false", description="f")
        attr = RoleAttributes(id=str(uuid7()), name="view-users")
        test_db_session.add_all([role_true, role_false, attr])
        await test_db_session.commit()
        test_db_session.add_all(
            [
                RoleMapper(user_id=test_user.id, role_id=role_true.id),
                RoleMapper(user_id=test_user.id, role_id=role_false.id),
                RoleAttributesMapper(role_id=role_true.id, attributes_id=attr.id, value=True),
                RoleAttributesMapper(role_id=role_false.id, attributes_id=attr.id, value=False),
            ]
        )
        await test_db_session.commit()

        attributes = await get_user_attributes(test_user.id, test_db_session)
        assert attributes["view-users"] is True

    @pytest.mark.asyncio
    async def test_raises_server_exception_on_error(self):
        db = AsyncMock()
        db.execute.side_effect = RuntimeError("db down")
        with pytest.raises(ServerException, match="Failed to get user attributes"):
            await get_user_attributes("user-1", db)


class TestRequirePermission:
    @pytest.mark.asyncio
    async def test_missing_db_raises_500(self):
        @require_permission([Permission.VIEW_USERS])
        async def protected(*, token, db=None):
            return "ok"

        with pytest.raises(HTTPException) as exc:
            await protected(token={"sub": "u1"})
        assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_super_admin_bypasses(self, test_db_session: AsyncSession, test_user: Users):
        role = Roles(
            id=str(uuid7()),
            name=settings.DEFAULT_SUPER_ADMIN_ROLE,
            description="super",
        )
        test_db_session.add(role)
        await test_db_session.commit()
        test_db_session.add(RoleMapper(user_id=test_user.id, role_id=role.id))
        await test_db_session.commit()

        @require_permission([Permission.MANAGE_USERS])
        async def protected(*, token, db):
            return "ok"

        result = await protected(token={"sub": test_user.id}, db=test_db_session)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_allows_when_user_has_permission(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        role = Roles(id=str(uuid7()), name="editor", description="e")
        attr = RoleAttributes(id=str(uuid7()), name="view-users")
        test_db_session.add_all([role, attr])
        await test_db_session.commit()
        test_db_session.add_all(
            [
                RoleMapper(user_id=test_user.id, role_id=role.id),
                RoleAttributesMapper(role_id=role.id, attributes_id=attr.id, value=True),
            ]
        )
        await test_db_session.commit()

        @require_permission([Permission.VIEW_USERS, Permission.MANAGE_USERS])
        async def protected(*, token, db):
            return "ok"

        result = await protected(token={"sub": test_user.id}, db=test_db_session)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_denies_without_permission(self, test_db_session: AsyncSession, test_user: Users):
        @require_permission(["view-users"])
        async def protected(*, token, db):
            return "ok"

        with pytest.raises(HTTPException) as exc:
            await protected(token={"sub": test_user.id}, db=test_db_session)
        assert exc.value.status_code == 403
        assert exc.value.detail == "Permission denied"
