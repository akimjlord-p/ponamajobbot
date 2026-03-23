import pytest

from config import RUN_LLM_TEST
from services.ai_service.parsing import AIReportParser
from utils.enums import ReportResultType
from services.ai_service.container import llm_connection


@pytest.mark.asyncio
async def test_parsing(llm_fixture):
    ai_report_parser = AIReportParser(llm_fixture, 'context')
    llm_fixture.ask_text.return_value = """
    {
      "report_result": "operations_created",
      "operations": [
        {
          "product_name": "product",
          "operation_type_name": "operation",
          "quantity": 1
        }
      ]
    }"""
    report_text = "report_text"
    result = await ai_report_parser.parse(report_text)
    assert result.report_result == ReportResultType.OPERATIONS_CREATED
    assert result.raw_operations[0].operation_type_name == "operation"
    assert result.raw_operations[0].quantity == 1
    assert result.raw_operations[0].product_name == "product"


@pytest.mark.asyncio
@pytest.mark.skipif(not RUN_LLM_TEST, reason="LLM test disabled")
async def test_parsing_with_real_llm_operations_created():
    ai_report_parser = AIReportParser(llm_connection, 'нет дополнительно контекста')
    report_text = "упаковал 5 ремней"
    result = await ai_report_parser.parse(report_text)
    assert result.report_result == ReportResultType.OPERATIONS_CREATED
    assert len(result.raw_operations) == 1
    assert result.raw_operations[0].operation_type_name == "упаковка"
    assert result.raw_operations[0].quantity == 5
    assert result.raw_operations[0].product_name in ['ремень', 'ремни']


@pytest.mark.asyncio
@pytest.mark.skipif(not RUN_LLM_TEST, reason="LLM test disabled")
async def test_parsing_with_real_llm_no_data():
    ai_report_parser = AIReportParser(llm_connection, 'нет дополнительно контекста')
    report_text = "семь восемь пять четыре"

    result = await ai_report_parser.parse(report_text)
    assert result.report_result == ReportResultType.NO_ACTIONABLE_DATA
    assert result.raw_operations == []
    assert result.reason == 'no_actionable_data'


@pytest.mark.asyncio
@pytest.mark.skipif(not RUN_LLM_TEST, reason="LLM test disabled")
async def test_parsing_with_real_llm_only_text():
    ai_report_parser = AIReportParser(llm_connection, 'нет дополнительно контекста')
    report_text = "сегодня были проблемы с погрузкой"

    result = await ai_report_parser.parse(report_text)
    assert result.report_result == ReportResultType.TEXT_ONLY
    assert result.raw_operations == []