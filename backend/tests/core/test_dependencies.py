from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from core.dependencies import get_db, get_sync_db


class _AsyncSessionCM:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class TestGetDb:
    @pytest.mark.asyncio
    async def test_yields_session(self):
        session = AsyncMock()
        with patch(
            "core.dependencies.AsyncSessionLocal",
            return_value=_AsyncSessionCM(session),
        ):
            agen = get_db()
            assert await agen.__anext__() is session
            await agen.aclose()

    @pytest.mark.asyncio
    async def test_http_exception_rolls_back(self):
        session = AsyncMock()
        with patch(
            "core.dependencies.AsyncSessionLocal",
            return_value=_AsyncSessionCM(session),
        ):
            agen = get_db()
            await agen.__anext__()
            with pytest.raises(HTTPException):
                await agen.athrow(HTTPException(status_code=400))
            session.rollback.assert_awaited()

    @pytest.mark.asyncio
    async def test_generic_exception_rolls_back(self):
        session = AsyncMock()
        with patch(
            "core.dependencies.AsyncSessionLocal",
            return_value=_AsyncSessionCM(session),
        ):
            agen = get_db()
            await agen.__anext__()
            with pytest.raises(RuntimeError, match="db down"):
                await agen.athrow(RuntimeError("db down"))
            session.rollback.assert_awaited()


class TestGetSyncDb:
    def test_yields_and_closes_session(self):
        session = MagicMock()
        with patch("core.dependencies.SessionLocal", return_value=session):
            gen = get_sync_db()
            assert next(gen) is session
            gen.close()
            session.close.assert_called_once()

    def test_rolls_back_on_error(self):
        session = MagicMock()
        with patch("core.dependencies.SessionLocal", return_value=session):
            gen = get_sync_db()
            next(gen)
            with pytest.raises(RuntimeError, match="db down"):
                gen.throw(RuntimeError("db down"))
            session.rollback.assert_called_once()
            session.close.assert_called_once()
