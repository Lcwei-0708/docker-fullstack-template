from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from uuid_utils import uuid7

from core.config import settings
from core.init_db import (
    create_default_admin,
    create_default_roles,
    create_role_attributes,
    init_database,
    is_already_initialized,
)
from core.permissions import get_attributes
from models.role_attributes import RoleAttributes
from models.role_mapper import RoleMapper
from models.roles import Roles
from models.users import Users


def _session_factory(engine):
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


class TestIsAlreadyInitialized:
    @pytest.mark.asyncio
    async def test_false_without_super_role(self, test_engine):
        factory = _session_factory(test_engine)
        with patch("core.init_db.AsyncSessionLocal", factory):
            assert await is_already_initialized() is False

    @pytest.mark.asyncio
    async def test_false_without_attributes(self, test_engine):
        factory = _session_factory(test_engine)
        async with factory() as db:
            db.add(
                Roles(
                    id=str(uuid7()),
                    name=settings.DEFAULT_SUPER_ADMIN_ROLE,
                    description="super",
                )
            )
            await db.commit()
        with patch("core.init_db.AsyncSessionLocal", factory):
            assert await is_already_initialized() is False

    @pytest.mark.asyncio
    async def test_false_without_super_user(self, test_engine):
        factory = _session_factory(test_engine)
        async with factory() as db:
            db.add(
                Roles(
                    id=str(uuid7()),
                    name=settings.DEFAULT_SUPER_ADMIN_ROLE,
                    description="super",
                )
            )
            db.add(RoleAttributes(id=str(uuid7()), name="view-users"))
            await db.commit()
        with patch("core.init_db.AsyncSessionLocal", factory):
            assert await is_already_initialized() is False

    @pytest.mark.asyncio
    async def test_true_when_seeded(self, test_engine):
        factory = _session_factory(test_engine)
        async with factory() as db:
            role = Roles(
                id=str(uuid7()),
                name=settings.DEFAULT_SUPER_ADMIN_ROLE,
                description="super",
            )
            user = Users(
                id=str(uuid7()),
                email="seeded@example.com",
                first_name="Seed",
                last_name="Admin",
                phone="0000000000",
                hash_password="hashed",
                status=True,
            )
            db.add_all(
                [role, user, RoleAttributes(id=str(uuid7()), name="view-users")]
            )
            await db.commit()
            db.add(RoleMapper(user_id=user.id, role_id=role.id))
            await db.commit()
        with patch("core.init_db.AsyncSessionLocal", factory):
            assert await is_already_initialized() is True


class TestCreateRoleAttributes:
    @pytest.mark.asyncio
    async def test_creates_and_updates_attributes(self, test_engine):
        factory = _session_factory(test_engine)
        async with factory() as db:
            db.add(RoleAttributes(id=str(uuid7()), name="view-users"))
            await db.commit()

        with patch("core.init_db.AsyncSessionLocal", factory):
            await create_role_attributes()
            await create_role_attributes()

        async with factory() as db:
            result = await db.execute(select(RoleAttributes))
            attrs = {row.name: row for row in result.scalars()}
        expected = {item["name"] for item in get_attributes()}
        assert set(attrs) == expected
        assert attrs["view-users"].group == "system-management"
        assert attrs["view-users"].category == "user-management"

    @pytest.mark.asyncio
    async def test_rolls_back_on_error(self, test_engine):
        factory = _session_factory(test_engine)
        with patch("core.init_db.AsyncSessionLocal", factory), patch(
            "core.init_db.get_attributes", side_effect=RuntimeError("boom")
        ):
            with pytest.raises(RuntimeError, match="boom"):
                await create_role_attributes()


class TestCreateDefaultRoles:
    @pytest.mark.asyncio
    async def test_creates_super_admin_and_user_roles(self, test_engine):
        factory = _session_factory(test_engine)
        with patch("core.init_db.AsyncSessionLocal", factory):
            await create_default_roles()
            await create_default_roles()

        async with factory() as db:
            result = await db.execute(select(Roles))
            names = {role.name for role in result.scalars()}
        assert names == {settings.DEFAULT_SUPER_ADMIN_ROLE, "user"}

    @pytest.mark.asyncio
    async def test_rolls_back_on_error(self, test_engine):
        factory = _session_factory(test_engine)
        with patch("core.init_db.AsyncSessionLocal", factory), patch(
            "sqlalchemy.ext.asyncio.session.AsyncSession.add",
            side_effect=RuntimeError("boom"),
        ):
            with pytest.raises(RuntimeError, match="boom"):
                await create_default_roles()


class TestCreateDefaultAdmin:
    @pytest.mark.asyncio
    async def test_skips_without_super_role(self, test_engine):
        factory = _session_factory(test_engine)
        with patch("core.init_db.AsyncSessionLocal", factory):
            await create_default_admin()
        async with factory() as db:
            result = await db.execute(select(Users))
            assert result.scalars().first() is None

    @pytest.mark.asyncio
    async def test_creates_admin_user(self, test_engine):
        factory = _session_factory(test_engine)
        with patch("core.init_db.AsyncSessionLocal", factory):
            await create_default_roles()
            await create_default_admin()

        async with factory() as db:
            user = (
                await db.execute(
                    select(Users).where(Users.email == settings.DEFAULT_ADMIN_EMAIL)
                )
            ).scalar_one()
            mapping = (
                await db.execute(
                    select(RoleMapper).where(RoleMapper.user_id == user.id)
                )
            ).scalar_one()
        assert user.email_verified is True
        assert mapping.role_id is not None

    @pytest.mark.asyncio
    async def test_skips_when_super_user_exists(self, test_engine):
        factory = _session_factory(test_engine)
        with patch("core.init_db.AsyncSessionLocal", factory):
            await create_default_roles()
            await create_default_admin()
            await create_default_admin()

        async with factory() as db:
            result = await db.execute(select(Users))
            assert len(result.scalars().all()) == 1

    @pytest.mark.asyncio
    async def test_assigns_role_to_existing_email(self, test_engine):
        factory = _session_factory(test_engine)
        with patch("core.init_db.AsyncSessionLocal", factory):
            await create_default_roles()

        async with factory() as db:
            user = Users(
                id=str(uuid7()),
                email=settings.DEFAULT_ADMIN_EMAIL,
                first_name="Existing",
                last_name="Admin",
                phone="1111111111",
                hash_password="hashed",
                status=True,
            )
            db.add(user)
            await db.commit()

            user_role = (
                await db.execute(select(Roles).where(Roles.name == "user"))
            ).scalar_one()
            db.add(RoleMapper(user_id=user.id, role_id=user_role.id))
            await db.commit()

        with patch("core.init_db.AsyncSessionLocal", factory):
            await create_default_admin()

        async with factory() as db:
            user = (
                await db.execute(
                    select(Users).where(Users.email == settings.DEFAULT_ADMIN_EMAIL)
                )
            ).scalar_one()
            super_role = (
                await db.execute(
                    select(Roles).where(Roles.name == settings.DEFAULT_SUPER_ADMIN_ROLE)
                )
            ).scalar_one()
            mappings = (
                await db.execute(
                    select(RoleMapper).where(RoleMapper.user_id == user.id)
                )
            ).scalars().all()
        assert user.first_name == "Existing"
        assert len(mappings) == 1
        assert mappings[0].role_id == super_role.id

    @pytest.mark.asyncio
    async def test_rolls_back_on_error(self, test_engine):
        factory = _session_factory(test_engine)
        with patch("core.init_db.AsyncSessionLocal", factory), patch(
            "core.init_db.select", side_effect=RuntimeError("boom")
        ):
            with pytest.raises(RuntimeError, match="boom"):
                await create_default_admin()


class _LockSessionCM:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class TestInitDatabase:
    @pytest.mark.asyncio
    async def test_skips_when_lock_not_acquired(self):
        session = AsyncMock()
        lock_result = MagicMock()
        lock_result.scalar.return_value = 0
        session.execute.return_value = lock_result
        with patch(
            "core.init_db.AsyncSessionLocal",
            return_value=_LockSessionCM(session),
        ), patch(
            "core.init_db.is_already_initialized", new_callable=AsyncMock
        ) as mock_initialized:
            await init_database()
        mock_initialized.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_already_initialized(self):
        session = AsyncMock()
        lock_result = MagicMock()
        lock_result.scalar.return_value = 1
        session.execute.return_value = lock_result
        with patch(
            "core.init_db.AsyncSessionLocal",
            return_value=_LockSessionCM(session),
        ), patch(
            "core.init_db.is_already_initialized",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "core.init_db.create_role_attributes", new_callable=AsyncMock
        ) as mock_attrs:
            await init_database()
        mock_attrs.assert_not_called()
        assert session.execute.await_count >= 2
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_seeds_when_lock_acquired(self):
        session = AsyncMock()
        lock_result = MagicMock()
        lock_result.scalar.return_value = 1
        session.execute.return_value = lock_result
        with patch(
            "core.init_db.AsyncSessionLocal",
            return_value=_LockSessionCM(session),
        ), patch(
            "core.init_db.is_already_initialized",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "core.init_db.create_role_attributes", new_callable=AsyncMock
        ) as mock_attrs, patch(
            "core.init_db.create_default_roles", new_callable=AsyncMock
        ) as mock_roles, patch(
            "core.init_db.create_default_admin", new_callable=AsyncMock
        ) as mock_admin:
            await init_database()
        mock_attrs.assert_awaited_once()
        mock_roles.assert_awaited_once()
        mock_admin.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_releases_lock_on_error(self):
        session = AsyncMock()
        lock_result = MagicMock()
        lock_result.scalar.return_value = 1
        session.execute.return_value = lock_result
        with patch(
            "core.init_db.AsyncSessionLocal",
            return_value=_LockSessionCM(session),
        ), patch(
            "core.init_db.is_already_initialized",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "core.init_db.create_role_attributes",
            new_callable=AsyncMock,
            side_effect=RuntimeError("seed failed"),
        ):
            with pytest.raises(RuntimeError, match="seed failed"):
                await init_database()
        session.commit.assert_awaited()
