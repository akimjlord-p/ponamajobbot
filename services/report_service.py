from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import WorkReport
from repositories.report_repository import ReportRepository
from repositories.user_repository import UserRepository
from services.operation_service import OperationService
from utils.apptime import apptime
from db.enums import ReportStatus, ReportResultType
from ai_service.parsing import parse


class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.report_repository = ReportRepository(self.session)
        self.user_repository = UserRepository(self.session)
        self.operation_service = OperationService(self.session)

    async def create_work_report(
        self,
        report_text: str,
        telegram_id: int,
        session_id: int,
    ) -> WorkReport | None:
        worker = await self.user_repository.get_by_telegram_id(telegram_id)
        if not worker:
            return None

        parsing_result = await parse(report_text, ReportResultType.OPERATIONS_CREATED)

        if parsing_result.report_result == ReportResultType.NO_ACTIONABLE_DATA:
            report = await self.report_repository.create(
                session_id=session_id,
                worker_id=worker.id,
                text=report_text,
                status=ReportStatus.SHOULD_BE_SENT_TO_ADMIN,
                created_at=apptime(),
                result_type=ReportResultType.NO_ACTIONABLE_DATA,
            )
            await self.session.commit()
            return report

        if parsing_result.report_result == ReportResultType.TEXT_ONLY:
            report = await self.report_repository.create(
                session_id=session_id,
                worker_id=worker.id,
                text=report_text,
                status=ReportStatus.PARSED,
                created_at=apptime(),
                result_type=ReportResultType.TEXT_ONLY,
            )
            await self.session.commit()
            return report

        report = await self.report_repository.create(
            session_id=session_id,
            worker_id=worker.id,
            text=report_text,
            status=ReportStatus.PARSED,
            created_at=apptime(),
            result_type=ReportResultType.OPERATIONS_CREATED,
        )

        total_amount = Decimal("0.00")

        for operation in parsing_result.operations:
            performed_operation = await self.operation_service.create_performed_operation(
                product_id=operation.product_id,
                operation_type_id=operation.operation_type_id,
                quantity=operation.quantity,
                worker_id=worker.id,
                session_id=session_id,
                report_id=report.id,
            )

            if performed_operation is not None and performed_operation.amount is not None:
                total_amount += performed_operation.amount

        await self.report_repository.set_total_amount(report.id, total_amount)
        await self.session.commit()
        return report