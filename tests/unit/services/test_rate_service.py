import pytest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from services.rate_service import RateService


@pytest.mark.asyncio
@patch("services.rate_service.appdate")
async def test_create_rate(mock_appdate, session_fixture):
    fake_date = "2026-03-18"
    mock_appdate.return_value = fake_date

    rate_service = RateService(session_fixture)

    rate_service.rate_repository = AsyncMock()
    rate_service.rate_repository.get_rate.return_value = None

    created_rate = SimpleNamespace(id=1, rate=Decimal("100"))
    rate_service.rate_repository.create.return_value = created_rate

    result = await rate_service.create_rate(1, 2, 100)

    rate_service.rate_repository.get_rate.assert_awaited_once_with(1, 2, fake_date)

    rate_service.rate_repository.create.assert_awaited_once_with(1, 2, Decimal("100"), fake_date)

    session_fixture.commit.assert_awaited_once()

    assert result is created_rate


@pytest.mark.asyncio
@patch("services.rate_service.appdate")
async def test_create_rate_with_existing_rate(mock_appdate, session_fixture):
    fake_date = "2026-03-18"
    mock_appdate.return_value = fake_date


    rate_service = RateService(session_fixture)

    fake_rate = SimpleNamespace()

    rate_service.rate_repository = AsyncMock()
    rate_service.rate_repository.get_rate.return_value = fake_rate

    result = await rate_service.create_rate(1, 2, 100)
    rate_service.rate_repository.get_rate.assert_awaited_once_with(1, 2, fake_date)

    rate_service.rate_repository.create.assert_not_awaited()
    session_fixture.commit.assert_not_awaited()
    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "product_return, operation_type_return, rate_return",
    [
        (None, SimpleNamespace(id=1), SimpleNamespace(id=1)),
        (SimpleNamespace(id=1), None, SimpleNamespace(id=1)),
        (SimpleNamespace(id=1), SimpleNamespace(id=1), None),
    ],
    ids=[
        "no_product",
        "no_operation_type",
        "no_rate",
    ],
)
async def test_update_rate_when_required_entity_missing(
        session_fixture,
        product_return,
        operation_type_return,
        rate_return,
):

    rate_service = RateService(session_fixture)

    rate_service.rate_repository = AsyncMock()
    rate_service.rate_repository.get_rate.return_value = rate_return

    rate_service.operation_repository = AsyncMock()
    rate_service.operation_repository.get_product_by_name.return_value = product_return
    rate_service.operation_repository.get_operation_type_by_name.return_value = operation_type_return

    result = await rate_service.update_rate("product_name", "operation_name", 100)

    assert result is None
    rate_service.rate_repository.update.assert_not_awaited()
    session_fixture.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_rate(session_fixture):
    rate_service = RateService(session_fixture)

    existing_rate = SimpleNamespace(id=1, rate=Decimal("99"))

    rate_service.rate_repository = AsyncMock()
    rate_service.rate_repository.get_rate.return_value = existing_rate
    rate_service.rate_repository.update.return_value = existing_rate

    rate_service.operation_repository = AsyncMock()
    rate_service.operation_repository.get_product_by_name.return_value = SimpleNamespace(id=1)
    rate_service.operation_repository.get_operation_type_by_name.return_value = SimpleNamespace(id=1)

    result = await rate_service.update_rate("product_name", "operation_name", Decimal('100'))

    assert result.rate == Decimal("100")
    rate_service.rate_repository.update.assert_awaited_once_with(existing_rate)
    session_fixture.commit.assert_awaited_once()
    assert result == existing_rate


@pytest.mark.parametrize(
    "product_return, operation_type_return, rate_return",
    [
        (None, SimpleNamespace(id=1), SimpleNamespace(id=1)),
        (SimpleNamespace(id=1), None, SimpleNamespace(id=1)),
        (SimpleNamespace(id=1), SimpleNamespace(id=1), None),
    ],
    ids=[
        "no_product",
        "no_operation_type",
        "no_rate",
    ],
)
@pytest.mark.asyncio
async def test_deactivate_rate_when_required_entity_missing(
        session_fixture,
        product_return,
        operation_type_return,
        rate_return,
):

    rate_service = RateService(session_fixture)

    rate_service.rate_repository = AsyncMock()
    rate_service.rate_repository.get_rate.return_value = rate_return

    rate_service.operation_repository = AsyncMock()
    rate_service.operation_repository.get_product_by_name.return_value = product_return
    rate_service.operation_repository.get_operation_type_by_name.return_value = operation_type_return

    result = await rate_service.deactivate_rate("product_name", "operation_name")

    assert result is None

    rate_service.rate_repository.deactivate.assert_not_awaited()
    session_fixture.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_deactivate_rate(session_fixture):
    rate_service = RateService(session_fixture)

    existing_rate = SimpleNamespace(id=1, rate=Decimal("100"), is_active=True)
    deactivated_rate = SimpleNamespace(id=1, rate=Decimal("100"), is_active=False)

    rate_service.rate_repository = AsyncMock()
    rate_service.rate_repository.get_rate.return_value = existing_rate
    rate_service.rate_repository.deactivate.return_value = deactivated_rate

    rate_service.operation_repository = AsyncMock()
    rate_service.operation_repository.get_product_by_name.return_value = SimpleNamespace(id=1)
    rate_service.operation_repository.get_operation_type_by_name.return_value = SimpleNamespace(id=1)


    result = await rate_service.deactivate_rate("product_name", "operation_name")

    assert result is deactivated_rate

    rate_service.rate_repository.deactivate.assert_awaited_once_with(existing_rate.id)
    rate_service.operation_repository.get_product_by_name.assert_awaited_once_with("product_name")
    rate_service.operation_repository.get_operation_type_by_name.assert_awaited_once_with("operation_name")
    session_fixture.commit.assert_awaited_once_with()









