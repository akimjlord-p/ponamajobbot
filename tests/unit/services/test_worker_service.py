from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.worker_service import WorkerService
from utils.enums import UserRole


@pytest.mark.asyncio
async def test_user_exists_returns_true_when_user_found(session_fixture):
    worker_service = WorkerService(session_fixture)
    worker_service.user_repo = AsyncMock()
    worker_service.user_repo.get_by_telegram_id.return_value = SimpleNamespace(id=1)

    result = await worker_service.user_exists(12345)

    assert result is True
    worker_service.user_repo.get_by_telegram_id.assert_awaited_once_with(12345)


@pytest.mark.asyncio
async def test_user_exists_returns_false_when_user_not_found(session_fixture):
    worker_service = WorkerService(session_fixture)
    worker_service.user_repo = AsyncMock()
    worker_service.user_repo.get_by_telegram_id.return_value = None

    result = await worker_service.user_exists(12345)

    assert result is False
    worker_service.user_repo.get_by_telegram_id.assert_awaited_once_with(12345)


@pytest.mark.asyncio
async def test_is_admin_returns_true_for_admin(session_fixture):
    worker_service = WorkerService(session_fixture)
    worker_service.user_repo = AsyncMock()
    worker_service.user_repo.get_by_telegram_id.return_value = SimpleNamespace(
        id=1,
        role=UserRole.ADMIN,
    )

    result = await worker_service.is_admin(12345)

    assert result is True
    worker_service.user_repo.get_by_telegram_id.assert_awaited_once_with(12345)


@pytest.mark.asyncio
async def test_is_admin_returns_false_for_non_admin(session_fixture):
    worker_service = WorkerService(session_fixture)
    worker_service.user_repo = AsyncMock()
    worker_service.user_repo.get_by_telegram_id.return_value = SimpleNamespace(
        id=1,
        role=UserRole.WORKER,
    )

    result = await worker_service.is_admin(12345)

    assert result is False
    worker_service.user_repo.get_by_telegram_id.assert_awaited_once_with(12345)


@pytest.mark.asyncio
async def test_is_admin_returns_false_when_user_not_found(session_fixture):
    worker_service = WorkerService(session_fixture)
    worker_service.user_repo = AsyncMock()
    worker_service.user_repo.get_by_telegram_id.return_value = None

    result = await worker_service.is_admin(12345)

    assert result is False
    worker_service.user_repo.get_by_telegram_id.assert_awaited_once_with(12345)
