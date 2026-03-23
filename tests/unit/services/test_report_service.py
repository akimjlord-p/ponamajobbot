from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from services.ai_service.parsing import ParsingResult
from services.report_service import ReportService
from utils.enums import ReportResultType, ReportStatus
from tests.conftest import session_fixture, report_service, ai_service_fixture


@pytest.mark.asyncio
async def test_normalize_operations_success(report_service):
    raw_operations = [
        SimpleNamespace(
            product_name="ремень",
            operation_type_name="упаковка",
            quantity=5,
        ),
        SimpleNamespace(
            product_name="куртка",
            operation_type_name="сборка",
            quantity=2,
        ),
    ]

    normalized_1 = SimpleNamespace(product=SimpleNamespace(id=1), operation=SimpleNamespace(id=10), quantity=5)
    normalized_2 = SimpleNamespace(product=SimpleNamespace(id=2), operation=SimpleNamespace(id=20), quantity=2)

    report_service.operation_normalizer_service.normalize_operation = AsyncMock(
        side_effect=[normalized_1, normalized_2]
    )

    result = await report_service._normalize_operations(raw_operations)

    assert result == [normalized_1, normalized_2]
    assert report_service.operation_normalizer_service.normalize_operation.await_count == 2


@pytest.mark.asyncio
async def test_normalize_operations_returns_none_if_one_operation_failed(report_service):
    raw_operations = [
        SimpleNamespace(
            product_name="ремень",
            operation_type_name="упаковка",
            quantity=5,
        ),
        SimpleNamespace(
            product_name="куртка",
            operation_type_name="сборка",
            quantity=2,
        ),
    ]

    normalized_1 = SimpleNamespace(product=SimpleNamespace(id=1), operation=SimpleNamespace(id=10), quantity=5)

    report_service.operation_normalizer_service.normalize_operation = AsyncMock(
        side_effect=[normalized_1, None]
    )

    result = await report_service._normalize_operations(raw_operations)

    assert result is None
    assert report_service.operation_normalizer_service.normalize_operation.await_count == 2


@pytest.mark.asyncio
async def test_generate_performed_operations_success(report_service):
    normalized_operations = [
        SimpleNamespace(
            product=SimpleNamespace(id=1),
            operation=SimpleNamespace(id=10),
            quantity=5,
        ),
        SimpleNamespace(
            product=SimpleNamespace(id=2),
            operation=SimpleNamespace(id=20),
            quantity=2,
        ),
    ]

    performed_1 = SimpleNamespace(amount=100)
    performed_2 = SimpleNamespace(amount=50)

    report_service.operation_service.create_performed_operation = AsyncMock(
        side_effect=[performed_1, performed_2]
    )

    result = await report_service._generate_performed_operations(
        normalized_operations=normalized_operations,
        worker_id=123,
        session_id=456,
        report_id=789,
    )

    assert result == [performed_1, performed_2]
    assert report_service.operation_service.create_performed_operation.await_count == 2


@pytest.mark.asyncio
async def test_generate_performed_operations_returns_none_if_one_creation_failed(report_service):
    normalized_operations = [
        SimpleNamespace(
            product=SimpleNamespace(id=1),
            operation=SimpleNamespace(id=10),
            quantity=5,
        ),
        SimpleNamespace(
            product=SimpleNamespace(id=2),
            operation=SimpleNamespace(id=20),
            quantity=2,
        ),
    ]

    performed_1 = SimpleNamespace(amount=100)

    report_service.operation_service.create_performed_operation = AsyncMock(
        side_effect=[performed_1, None]
    )

    result = await report_service._generate_performed_operations(
        normalized_operations=normalized_operations,
        worker_id=123,
        session_id=456,
        report_id=789,
    )

    assert result is None
    assert report_service.operation_service.create_performed_operation.await_count == 2


def test_count_total_amount(report_service):
    performed_operations = [
        SimpleNamespace(amount=10),
        SimpleNamespace(amount=20),
        SimpleNamespace(amount=30),
    ]

    result = report_service._count_total_amount(performed_operations)

    assert result == 60


@pytest.mark.asyncio
async def test_create_work_report_returns_none_if_worker_not_found(report_service, ai_service_fixture, session_fixture):
    report_service.user_repository.get_by_telegram_id = AsyncMock(return_value=None)

    result = await report_service.create_work_report(
        report_text="отчет",
        telegram_id=111,
        session_id=222,
    )

    assert result is None
    session_fixture.commit.assert_not_awaited()
    ai_service_fixture.parse_report.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_work_report_creates_admin_review_report_for_no_actionable_data(
    report_service,
    ai_service_fixture,
    session_fixture,
):
    worker = SimpleNamespace(id=1)
    created_report = SimpleNamespace(id=100, status=ReportStatus.SHOULD_BE_SENT_TO_ADMIN)

    report_service.user_repository.get_by_telegram_id = AsyncMock(return_value=worker)
    report_service._build_parsing_context = AsyncMock(return_value="context")
    ai_service_fixture.parse_report.return_value = ParsingResult(
        ReportResultType.NO_ACTIONABLE_DATA,
        reason="no_actionable_data",
    )
    report_service._create_report_for_admin_review = AsyncMock(return_value=created_report)

    result = await report_service.create_work_report(
        report_text="непонятный отчет",
        telegram_id=111,
        session_id=222,
    )

    assert result == created_report
    report_service._create_report_for_admin_review.assert_awaited_once_with(
        session_id=222,
        worker_id=1,
        report_text="непонятный отчет",
    )
    session_fixture.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_work_report_creates_text_only_report(
    report_service,
    ai_service_fixture,
    session_fixture,
):
    worker = SimpleNamespace(id=1)
    created_report = SimpleNamespace(id=101, status=ReportStatus.PARSED)

    report_service.user_repository.get_by_telegram_id = AsyncMock(return_value=worker)
    report_service._build_parsing_context = AsyncMock(return_value="context")
    ai_service_fixture.parse_report.return_value = ParsingResult(
        ReportResultType.TEXT_ONLY,
    )
    report_service._create_report_with_only_text = AsyncMock(return_value=created_report)

    result = await report_service.create_work_report(
        report_text="сегодня были проблемы с погрузкой",
        telegram_id=111,
        session_id=222,
    )

    assert result == created_report
    report_service._create_report_with_only_text.assert_awaited_once_with(
        session_id=222,
        worker_id=1,
        report_text="сегодня были проблемы с погрузкой",
    )
    session_fixture.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_work_report_creates_admin_review_report_if_normalization_failed(
    report_service,
    ai_service_fixture,
    session_fixture,
):
    worker = SimpleNamespace(id=1)
    raw_operations = [
        SimpleNamespace(
            product_name="ремень",
            operation_type_name="упаковка",
            quantity=5,
        )
    ]
    created_report = SimpleNamespace(id=102, status=ReportStatus.SHOULD_BE_SENT_TO_ADMIN)

    report_service.user_repository.get_by_telegram_id = AsyncMock(return_value=worker)
    report_service._build_parsing_context = AsyncMock(return_value="context")
    ai_service_fixture.parse_report.return_value = ParsingResult(
        ReportResultType.OPERATIONS_CREATED,
        operations=raw_operations,
    )
    report_service._normalize_operations = AsyncMock(return_value=None)
    report_service._create_report_for_admin_review = AsyncMock(return_value=created_report)

    result = await report_service.create_work_report(
        report_text="упаковал 5 ремней",
        telegram_id=111,
        session_id=222,
    )

    assert result == created_report
    report_service._normalize_operations.assert_awaited_once_with(raw_operations)
    report_service._create_report_for_admin_review.assert_awaited_once_with(
        session_id=222,
        worker_id=1,
        report_text="упаковал 5 ремней",
    )
    session_fixture.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_work_report_updates_report_if_performed_operations_generation_failed(
    report_service,
    ai_service_fixture,
    session_fixture,
):
    worker = SimpleNamespace(id=1)
    raw_operations = [
        SimpleNamespace(
            product_name="ремень",
            operation_type_name="упаковка",
            quantity=5,
        )
    ]
    normalized_operations = [
        SimpleNamespace(
            product=SimpleNamespace(id=10),
            operation=SimpleNamespace(id=20),
            quantity=5,
        )
    ]
    report = SimpleNamespace(id=103)

    report_service.user_repository.get_by_telegram_id = AsyncMock(return_value=worker)
    report_service._build_parsing_context = AsyncMock(return_value="context")
    ai_service_fixture.parse_report.return_value = ParsingResult(
        ReportResultType.OPERATIONS_CREATED,
        operations=raw_operations,
    )
    report_service._normalize_operations = AsyncMock(return_value=normalized_operations)
    report_service._create_report_with_operations = AsyncMock(return_value=report)
    report_service._generate_performed_operations = AsyncMock(return_value=None)
    report_service.report_repository.update = AsyncMock()

    result = await report_service.create_work_report(
        report_text="упаковал 5 ремней",
        telegram_id=111,
        session_id=222,
    )

    assert result == report
    report_service.report_repository.update.assert_awaited_once_with(
        report,
        status=ReportStatus.SHOULD_BE_SENT_TO_ADMIN,
        result_type=ReportResultType.NO_ACTIONABLE_DATA,
    )
    session_fixture.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_work_report_success_with_operations(
    report_service,
    ai_service_fixture,
    session_fixture,
):
    worker = SimpleNamespace(id=1)
    raw_operations = [
        SimpleNamespace(
            product_name="ремень",
            operation_type_name="упаковка",
            quantity=5,
        )
    ]
    normalized_operations = [
        SimpleNamespace(
            product=SimpleNamespace(id=10),
            operation=SimpleNamespace(id=20),
            quantity=5,
        )
    ]
    performed_operations = [
        SimpleNamespace(amount=150),
        SimpleNamespace(amount=50),
    ]
    report = SimpleNamespace(id=104)

    report_service.user_repository.get_by_telegram_id = AsyncMock(return_value=worker)
    report_service._build_parsing_context = AsyncMock(return_value="context")
    ai_service_fixture.parse_report.return_value = ParsingResult(
        ReportResultType.OPERATIONS_CREATED,
        operations=raw_operations,
    )
    report_service._normalize_operations = AsyncMock(return_value=normalized_operations)
    report_service._create_report_with_operations = AsyncMock(return_value=report)
    report_service._generate_performed_operations = AsyncMock(return_value=performed_operations)
    report_service.report_repository.set_total_amount = AsyncMock()

    result = await report_service.create_work_report(
        report_text="упаковал 5 ремней",
        telegram_id=111,
        session_id=222,
    )

    assert result == report
    report_service.report_repository.set_total_amount.assert_awaited_once_with(
        104,
        200,
    )
    session_fixture.commit.assert_awaited_once()