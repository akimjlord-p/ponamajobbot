from db.enums import ReportResultType


class ParsedOperation:
    def __init__(
        self,
        product_id: int,
        operation_type_id: int,
        quantity: int,
    ) -> None:
        self.product_id = product_id
        self.operation_type_id = operation_type_id
        self.quantity = quantity


class ParsingResult:
    def __init__(
        self,
        report_result: ReportResultType,
        operations: list[ParsedOperation] | None = None,
    ) -> None:
        self.report_result = report_result
        self.operations = operations or []


async def parse(text: str, parse_type: ReportResultType) -> ParsingResult:
    if parse_type == ReportResultType.OPERATIONS_CREATED:
        return ParsingResult(
            ReportResultType.OPERATIONS_CREATED,
            operations=[
                ParsedOperation(product_id=1, operation_type_id=1, quantity=3),
                ParsedOperation(product_id=2, operation_type_id=2, quantity=5),
            ],
        )

    if parse_type == ReportResultType.TEXT_ONLY:
        return ParsingResult(ReportResultType.TEXT_ONLY)

    return ParsingResult(ReportResultType.NO_ACTIONABLE_DATA)