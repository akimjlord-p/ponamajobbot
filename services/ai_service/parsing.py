from services.ai_service.llm_connection import LLMConnection
from utils.enums import ReportResultType
import json
from .prompts import Prompts


class ParsedOperationRaw:
    def __init__(
        self,
        product_name: str,
        operation_type_name: str,
        quantity: int,
    ) -> None:
        self.product_name = product_name
        self.operation_type_name = operation_type_name
        self.quantity = quantity


class ParsingResult:
    def __init__(
        self,
        report_result: ReportResultType,
        operations: list[ParsedOperationRaw] | None = None,
    ) -> None:
        self.report_result = report_result
        self.raw_operations = operations or []

class AIReportParser:
    def __init__(self, llm_connection: LLMConnection, parsing_context: str) -> None:
        self.llm_connection = llm_connection
        self.parsing_context = parsing_context

    async def parse(self, text: str) -> ParsingResult:
        prompt = Prompts.get_report_parsing_prompt(text, self.parsing_context)
        response = await self.llm_connection.ask_text(prompt)

        if not response:
            return ParsingResult(ReportResultType.NO_ACTIONABLE_DATA,)
        try:
            json_data = self._extract_json(response)
        except:
            return ParsingResult(ReportResultType.NO_ACTIONABLE_DATA)

        report_result_type_raw = json_data.get("report_result_type", None)

        if not report_result_type_raw:
            return ParsingResult(ReportResultType.NO_ACTIONABLE_DATA)

        try:
            report_result_type = ReportResultType(report_result_type_raw)
        except:
            return ParsingResult(ReportResultType.NO_ACTIONABLE_DATA)

        if report_result_type == ReportResultType.TEXT_ONLY:
            return ParsingResult(ReportResultType.TEXT_ONLY)

        elif report_result_type == ReportResultType.NO_ACTIONABLE_DATA:
            return ParsingResult(ReportResultType.NO_ACTIONABLE_DATA)

        else:
            operations_data = json_data.get("operations", None)


        if not operations_data:
            return ParsingResult(ReportResultType.NO_ACTIONABLE_DATA)

        operations: list[ParsedOperationRaw] = []
        for operation in operations_data:
            product_name = operation.get("product_name", None)
            operation_type_name = operation.get("operation_type_name", None)
            quantity = operation.get("quantity", None)

            if not product_name or not operation_type_name or not quantity:
                return ParsingResult(ReportResultType.NO_ACTIONABLE_DATA)

            try:
                quantity = int(quantity)
            except:
                return ParsingResult(ReportResultType.NO_ACTIONABLE_DATA)


            operations.append(ParsedOperationRaw(product_name, operation_type_name, quantity))

        return ParsingResult(report_result_type, operations)


    @staticmethod
    def _extract_json(raw_text: str) -> dict:
        text = raw_text.strip()

        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        return json.loads(text)