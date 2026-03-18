from datetime import timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import WorkReport
from repositories.ai_repository import AiRepository
from repositories.operation_repository import OperationRepository
from repositories.report_repository import ReportRepository
from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository
from services.operation_service import (
    OperationService,
    OperationNormalizerService,
    NormalizedOperation,
)
from utils.apptime import apptime
from utils.enums import ReportStatus, ReportResultType
from ai_service.service import AIService


class ReportService:
    def __init__(self, session: AsyncSession, ai_service: AIService):
        self.session = session
        self.report_repository = ReportRepository(self.session)
        self.user_repository = UserRepository(self.session)
        self.operation_service = OperationService(self.session)
        self.operation_repository = OperationRepository(self.session)
        self.session_repository = SessionRepository(self.session)
        self.ai_service = ai_service
        self.ai_repository = AiRepository(self.session)
        self.operation_normalizer_service = OperationNormalizerService(self.session)

    async def create_work_report(
        self,
        report_text: str,
        telegram_id: int,
        session_id: int,
    ) -> WorkReport | None:
        worker = await self.user_repository.get_by_telegram_id(telegram_id)
        if not worker:
            return None

        parsing_contexts = await self.ai_repository.get_active_parsing_contexts()
        parsing_context = "\n".join([item.text for item in parsing_contexts])

        parsing_result = await self.ai_service.parse_report(
            parsing_context=parsing_context,
            text=report_text,
        )

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

        normalized_operations: list[NormalizedOperation] = []

        for raw_operation in parsing_result.raw_operations:
            normalized_operation = await self.operation_normalizer_service.normalize_operation(
                raw_operation.product_name,
                raw_operation.operation_type_name,
                raw_operation.quantity,
            )

            if not normalized_operation:
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

            normalized_operations.append(normalized_operation)

        report = await self.report_repository.create(
            session_id=session_id,
            worker_id=worker.id,
            text=report_text,
            status=ReportStatus.PARSED,
            created_at=apptime(),
            result_type=ReportResultType.OPERATIONS_CREATED,
        )

        total_amount = Decimal("0.00")

        for operation in normalized_operations:
            performed_operation = await self.operation_service.create_performed_operation(
                product_id=operation.product.id,
                operation_type_id=operation.operation.id,
                quantity=operation.quantity,
                worker_id=worker.id,
                session_id=session_id,
                report_id=report.id,
            )

            if not performed_operation:
                await self.report_repository.update(
                    report,
                    status=ReportStatus.SHOULD_BE_SENT_TO_ADMIN,
                    result_type=ReportResultType.NO_ACTIONABLE_DATA,
                )
                await self.session.commit()
                return report

            if performed_operation.amount is not None:
                total_amount += performed_operation.amount

        await self.report_repository.set_total_amount(report.id, total_amount)
        await self.session.commit()
        return report

    async def get_today_reports_with_operations(self) -> list[dict] | None:
        today = apptime().date()
        reports = await self.report_repository.get_reports_in_range(
            today,
            today + timedelta(days=1),
        )

        if not reports:
            return None

        result: list[dict] = []

        for report in reports:
            operations = await self.operation_repository.get_operations_by_report(report.id)
            work_session = await self.session_repository.get_by_worker_and_date(
                report.worker_id,
                today,
            )

            duration = None
            if work_session and work_session.ended_at:
                duration = (work_session.ended_at - work_session.started_at).total_seconds()

            result.append(
                {
                    "report": report,
                    "operations": operations,
                    "duration": duration,
                }
            )

        return result