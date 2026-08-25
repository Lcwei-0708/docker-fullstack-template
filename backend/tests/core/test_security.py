from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import (
    clear_user_all_sessions,
    create_access_token,
    create_csrf_token,
    create_email_verification_token,
    create_password_reset_token,
    extend_session_ttl,
    get_token,
    hash_password,
    verify_email_verification_token,
    verify_password,
    verify_password_reset_token,
    verify_session,
    verify_token,
)
from models.user_sessions import UserSessions
from models.users import Users
from utils.custom_exception import ServerException


def _decode(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


class TestPasswordHashing:
    @pytest.mark.asyncio
    async def test_hash_and_verify_password(self):
        hashed = await hash_password("Secret123!")
        assert hashed != "Secret123!"
        assert await verify_password("Secret123!", hashed)
        assert not await verify_password("wrong", hashed)


class TestCreateTokens:
    @pytest.mark.asyncio
    async def test_create_access_token(self):
        token = await create_access_token({"sub": "user-1", "sid": "sess-1"})
        payload = _decode(token)
        assert payload["sub"] == "user-1"
        assert payload["sid"] == "sess-1"
        assert "exp" in payload
        assert "iat" in payload

    @pytest.mark.asyncio
    async def test_create_password_reset_token(self):
        token = await create_password_reset_token("user-1", "a@b.c")
        payload = _decode(token)
        assert payload["token_type"] == "password_reset"
        assert payload["force_change_password"] is True
        assert payload["sub"] == "user-1"
        assert payload["email"] == "a@b.c"

    @pytest.mark.asyncio
    async def test_create_password_reset_token_server_error(self):
        with patch("core.security.jwt.encode", side_effect=RuntimeError("encode failed")):
            with pytest.raises(ServerException, match="Failed to create password reset token"):
                await create_password_reset_token("user-1", "a@b.c")

    @pytest.mark.asyncio
    async def test_create_csrf_token(self):
        token = await create_csrf_token("sess-1")
        payload = _decode(token)
        assert payload["token_type"] == "csrf"
        assert payload["sid"] == "sess-1"

    @pytest.mark.asyncio
    async def test_create_csrf_token_server_error(self):
        with patch("core.security.jwt.encode", side_effect=RuntimeError("encode failed")):
            with pytest.raises(ServerException, match="Failed to create CSRF token"):
                await create_csrf_token("sess-1")

    @pytest.mark.asyncio
    async def test_create_email_verification_token(self):
        token = await create_email_verification_token(
            "user-1", "a@b.c", "registration"
        )
        payload = _decode(token)
        assert payload["token_type"] == "email_verification"
        assert payload["verification_type"] == "registration"
        assert payload["sub"] == "user-1"

    @pytest.mark.asyncio
    async def test_create_email_verification_token_server_error(self):
        with patch("core.security.jwt.encode", side_effect=RuntimeError("encode failed")):
            with pytest.raises(
                ServerException, match="Failed to create email verification token"
            ):
                await create_email_verification_token("user-1", "a@b.c", "email_change")


class TestGetToken:
    @pytest.mark.asyncio
    async def test_get_token_missing_credentials(self):
        with pytest.raises(HTTPException) as exc:
            await get_token(credentials=None)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_token_returns_credentials(self):
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="raw-token"
        )
        assert await get_token(credentials=credentials) == "raw-token"


class TestVerifySession:
    @pytest.mark.asyncio
    async def test_verify_session_success(self):
        redis_client = AsyncMock()
        redis_client.get.return_value = str(
            {"access_token": "tok", "user_id": "u1"}
        )
        data = await verify_session("sid-1", "tok", redis_client)
        assert data["access_token"] == "tok"
        redis_client.get.assert_awaited_once_with("session:sid-1")

    @pytest.mark.asyncio
    async def test_verify_session_missing(self):
        redis_client = AsyncMock()
        redis_client.get.return_value = None
        with pytest.raises(HTTPException) as exc:
            await verify_session("sid-1", "tok", redis_client)
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid or expired session"

    @pytest.mark.asyncio
    async def test_verify_session_invalid_data(self):
        redis_client = AsyncMock()
        redis_client.get.return_value = "not-a-dict"
        with pytest.raises(HTTPException) as exc:
            await verify_session("sid-1", "tok", redis_client)
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid or expired session"

    @pytest.mark.asyncio
    async def test_verify_session_token_mismatch(self):
        redis_client = AsyncMock()
        redis_client.get.return_value = str({"access_token": "other"})
        with pytest.raises(HTTPException) as exc:
            await verify_session("sid-1", "tok", redis_client)
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid or expired token"


class TestVerifyToken:
    @pytest.mark.asyncio
    async def test_verify_token_success(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        token = await create_access_token({"sub": test_user.id, "sid": "sess-1"})
        redis_client = AsyncMock()
        redis_client.get.return_value = str({"access_token": token})
        payload = await verify_token(
            token=token, redis_client=redis_client, db=test_db_session
        )
        assert payload["sub"] == test_user.id
        assert payload["sid"] == "sess-1"

    @pytest.mark.asyncio
    async def test_verify_token_missing_session_id(self, test_db_session: AsyncSession):
        token = await create_access_token({"sub": "user-1"})
        with pytest.raises(HTTPException) as exc:
            await verify_token(
                token=token, redis_client=AsyncMock(), db=test_db_session
            )
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_token_disabled_account(
        self, test_db_session: AsyncSession, test_user: Users
    ):
        test_user.status = False
        await test_db_session.commit()
        token = await create_access_token({"sub": test_user.id, "sid": "sess-1"})
        redis_client = AsyncMock()
        redis_client.get.return_value = str({"access_token": token})
        with pytest.raises(HTTPException) as exc:
            await verify_token(
                token=token, redis_client=redis_client, db=test_db_session
            )
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_verify_token_invalid_jwt(self, test_db_session: AsyncSession):
        with pytest.raises(HTTPException) as exc:
            await verify_token(
                token="not-a-jwt", redis_client=AsyncMock(), db=test_db_session
            )
        assert exc.value.status_code == 401


class TestVerifyPasswordResetToken:
    @pytest.mark.asyncio
    async def test_valid_token(self):
        token = await create_password_reset_token("user-1", "a@b.c")
        result = await verify_password_reset_token(token=token)
        assert result["sub"] == "user-1"
        assert result["email"] == "a@b.c"
        assert result["token"] == token

    @pytest.mark.asyncio
    async def test_wrong_token_type(self):
        token = await create_csrf_token("sess-1")
        with pytest.raises(HTTPException) as exc:
            await verify_password_reset_token(token=token)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_force_change_password(self):
        token = jwt.encode(
            {
                "sub": "user-1",
                "email": "a@b.c",
                "token_type": "password_reset",
                "exp": datetime.now().astimezone() + timedelta(minutes=5),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc:
            await verify_password_reset_token(token=token)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_payload(self):
        with patch(
            "core.security.jwt.decode",
            return_value={
                "sub": "user-1",
                "email": "a@b.c",
                "token_type": "password_reset",
                "force_change_password": True,
                "exp": 1,
            },
        ):
            with pytest.raises(HTTPException) as exc:
                await verify_password_reset_token(token="tok")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_payload_fields(self):
        with patch(
            "core.security.jwt.decode",
            return_value={
                "token_type": "password_reset",
                "force_change_password": True,
                "exp": datetime.now().astimezone().timestamp() + 60,
            },
        ):
            with pytest.raises(HTTPException) as exc:
                await verify_password_reset_token(token="tok")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_jwt(self):
        with pytest.raises(HTTPException) as exc:
            await verify_password_reset_token(token="bad")
        assert exc.value.status_code == 401


class TestVerifyEmailVerificationToken:
    @pytest.mark.asyncio
    async def test_valid_token(self):
        token = await create_email_verification_token(
            "user-1", "a@b.c", "email_change"
        )
        result = await verify_email_verification_token(token=token)
        assert result["verification_type"] == "email_change"
        assert result["sub"] == "user-1"

    @pytest.mark.asyncio
    async def test_wrong_token_type(self):
        token = await create_password_reset_token("user-1", "a@b.c")
        with pytest.raises(HTTPException) as exc:
            await verify_email_verification_token(token=token)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_verification_type(self):
        with patch(
            "core.security.jwt.decode",
            return_value={
                "sub": "user-1",
                "email": "a@b.c",
                "token_type": "email_verification",
                "verification_type": "unknown",
                "exp": datetime.now().astimezone().timestamp() + 60,
            },
        ):
            with pytest.raises(HTTPException) as exc:
                await verify_email_verification_token(token="tok")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_payload(self):
        with patch(
            "core.security.jwt.decode",
            return_value={
                "sub": "user-1",
                "email": "a@b.c",
                "token_type": "email_verification",
                "verification_type": "registration",
                "exp": 1,
            },
        ):
            with pytest.raises(HTTPException) as exc:
                await verify_email_verification_token(token="tok")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_payload_fields(self):
        with patch(
            "core.security.jwt.decode",
            return_value={
                "token_type": "email_verification",
                "verification_type": "registration",
                "exp": datetime.now().astimezone().timestamp() + 60,
            },
        ):
            with pytest.raises(HTTPException) as exc:
                await verify_email_verification_token(token="tok")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_jwt(self):
        with pytest.raises(HTTPException) as exc:
            await verify_email_verification_token(token="bad")
        assert exc.value.status_code == 401


class TestSessionHelpers:
    @pytest.mark.asyncio
    async def test_extend_session_ttl_success(self):
        redis_client = AsyncMock()
        session_data = {"access_token": "tok"}
        await extend_session_ttl(redis_client, "sid-1", session_data)
        redis_client.setex.assert_awaited_once()
        key, ttl, value = redis_client.setex.await_args.args
        assert key == "session:sid-1"
        assert ttl == settings.SESSION_EXPIRE_MINUTES * 60
        assert "last_activity" in session_data
        assert "tok" in value

    @pytest.mark.asyncio
    async def test_extend_session_ttl_swallows_error(self):
        redis_client = AsyncMock()
        redis_client.setex.side_effect = RuntimeError("redis down")
        await extend_session_ttl(redis_client, "sid-1", {})

    @pytest.mark.asyncio
    async def test_clear_user_all_sessions(
        self,
        test_db_session: AsyncSession,
        test_user: Users,
        test_user_session: UserSessions,
    ):
        redis_client = AsyncMock()
        result = await clear_user_all_sessions(
            test_db_session, redis_client, test_user.id
        )
        assert result is True
        redis_client.delete.assert_awaited()
        keys = redis_client.delete.await_args.args
        assert f"session:{test_user_session.id}" in keys
        assert f"csrf:{test_user_session.id}" in keys

        refreshed = await test_db_session.get(UserSessions, test_user_session.id)
        assert refreshed.is_active is False

    @pytest.mark.asyncio
    async def test_clear_user_all_sessions_keeps_excluded(
        self,
        test_db_session: AsyncSession,
        test_user: Users,
        test_user_session: UserSessions,
    ):
        redis_client = AsyncMock()
        result = await clear_user_all_sessions(
            test_db_session,
            redis_client,
            test_user.id,
            exclude_session_id=test_user_session.id,
        )
        assert result is True
        redis_client.delete.assert_not_called()
        refreshed = await test_db_session.get(UserSessions, test_user_session.id)
        assert refreshed.is_active is True

    @pytest.mark.asyncio
    async def test_clear_user_all_sessions_server_error(self):
        db = MagicMock()
        db.execute = AsyncMock(side_effect=RuntimeError("db down"))
        with pytest.raises(ServerException, match="Failed to logout all devices"):
            await clear_user_all_sessions(db, AsyncMock(), "user-1")
