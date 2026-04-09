from datetime import timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import WorkReport, WorkerPerformedOperation
from repositories.ai_repository import AiRepository
from repositories.operation_repository import OperationRepository
from repositories.report_repository import ReportRepository
from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository
from services.ai_service.parsing import ParsedOperationRaw
from services.operation_service import (
    OperationService,
    OperationNormalizerService,
    NormalizedOperation,
)
from utils.apptime import apptime
from utils.enums import ReportStatus, ReportResultType
from services.ai_service.service import AIService
from utils.logger import get_logger


logger = get_logger(__name__)


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

    async def _build_parsing_context(self) -> str | None:
        parsing_contexts = await self.ai_repository.get_active_parsing_contexts()
        parsing_context = "\n".join([item.text for item in parsing_contexts])
        return parsing_context

    async def _create_report_for_admin_review(self,
                                              session_id: int,
                                              worker_id: int,
                                              report_text: str) -> WorkReport | None:
        report = await self.report_repository.create(session_id=session_id,
                                                     worker_id=worker_id,
                                                     text=report_text,
                                                     status=ReportStatus.SHOULD_BE_SENT_TO_ADMIN,
                                                     created_at=apptime(),
                                                     result_type=ReportResultType.NO_ACTIONABLE_DATA
                                                     )
        return report

    async def _create_report_with_only_text(self,
                                            session_id: int,
                                            worker_id: int,
                                            report_text: str) -> WorkReport | None:
        report = await self.report_repository.create(session_id=session_id,
                                                     worker_id=worker_id,
                                                     text=report_text,
                                                     status=ReportStatus.PARSED,
                                                     created_at=apptime(),
                                                     result_type=ReportResultType.TEXT_ONLY)
        return report

    async def _create_report_with_operations(self,
                                             session_id: int,
                                             worker_id: int,
                                             report_text: str) -> WorkReport | None:
        report = await self.report_repository.create(session_id=session_id,
                                                     worker_id=worker_id,
                                                     text=report_text,
                                                     status=ReportStatus.PARSED,
                                                     created_at=apptime(),
                                                     result_type=ReportResultType.OPERATIONS_CREATED)
        return report

    async def _normalize_operations(self, raw_operations: list[ParsedOperationRaw]) -> list[NormalizedOperation] | None:
        normalized_operations: list[NormalizedOperation] = []
        for raw_operation in raw_operations:
            normalized_operation = await self.operation_normalizer_service.normalize_operation(
                raw_operation.product_name,
                raw_operation.operation_type_name,
                raw_operation.quantity,
            )
            if not normalized_operation:
                return None
            normalized_operations.append(normalized_operation)
        return normalized_operations

    async def _generate_performed_operations(self, normalized_operations: list[NormalizedOperation], worker_id: int, session_id: int, report_id: int) -> list[WorkerPerformedOperation] | None:
        performed_operations: list[WorkerPerformedOperation] = []
        for normalized_operation in normalized_operations:
            performed_operation = await self.operation_service.create_performed_operation(
                normalized_operation.product.id,
                normalized_operation.operation.id,
                normalized_operation.quantity,
                worker_id,
                session_id,
                report_id
            )
            if not performed_operation:
                return None
            performed_operations.append(performed_operation)
        return performed_operations

    @staticmethod
    def _count_total_amount(performed_operations: list[WorkerPerformedOperation]) -> Decimal:
        total_amount = Decimal("0.00")
        for performed_operation in performed_operations:
            total_amount += performed_operation.amount
        return total_amount



    async def create_work_report(
        self,
        report_text: str,
        telegram_id: int,
        session_id: int,
    ) -> WorkReport | None:
        logger.info(
            "Create work report requested: telegram_id=%s session_id=%s text_len=%s",
            telegram_id,
            session_id,
            len(report_text),
        )

        worker = await self.user_repository.get_by_telegram_id(telegram_id)
        if not worker:
            logger.warning("Create work report failed: worker not found telegram_id=%s", telegram_id)
            return None

        parsing_context = await self._build_parsing_context()

        parsing_result = await self.ai_service.parse_report(
            parsing_context=parsing_context,
            text=report_text,
        )
        logger.debug("Report parsing result: result_type=%s", parsing_result.report_result.value)

        if parsing_result.report_result == ReportResultType.NO_ACTIONABLE_DATA:
            report = await self._create_report_for_admin_review(session_id=session_id,
                                                                worker_id=worker.id,
                                                                report_text=report_text)
            await self.session.commit()
            logger.info("Report created for admin review: report_id=%s worker_id=%s", report.id, worker.id)
            return report

        if parsing_result.report_result == ReportResultType.TEXT_ONLY:
            report = await self._create_report_with_only_text(session_id=session_id,
                                                              worker_id=worker.id,
                                                              report_text=report_text
                                                              )
            await self.session.commit()
            logger.info("Text-only report created: report_id=%s worker_id=%s", report.id, worker.id)
            return report

        normalized_operations = await self._normalize_operations(parsing_result.raw_operations)
        if not normalized_operations:
            report = await self._create_report_for_admin_review(
                session_id=session_id,
                worker_id=worker.id,
                report_text=report_text
            )
            await self.session.commit()
            logger.warning("Report created for admin review: normalization failed report_id=%s", report.id)
            return report


        report = await self._create_report_with_operations(
            session_id=session_id,
            worker_id=worker.id,
            report_text=report_text,
        )

        performed_operations = await self._generate_performed_operations(
            normalized_operations=normalized_operations,
            worker_id=worker.id,
            session_id=session_id,
            report_id=report.id,
        )
        if not performed_operations:
            await self.report_repository.update(
                report,
                status=ReportStatus.SHOULD_BE_SENT_TO_ADMIN,
                result_type=ReportResultType.NO_ACTIONABLE_DATA,
            )
            await self.session.commit()
            logger.warning("Report updated for admin review: no operations created report_id=%s", report.id)
            return report

        total_amount = self._count_total_amount(performed_operations)

        await self.report_repository.set_total_amount(report.id, total_amount)
        await self.session.commit()
        logger.info(
            "Report created with operations: report_id=%s operations=%s total_amount=%s",
            report.id,
            len(performed_operations),
            total_amount,
        )
        return report

    async def get_today_reports_with_operations(self) -> list[dict] | None:
        today = apptime().date()
        reports = await self.report_repository.get_reports_in_range(
            today,
            today + timedelta(days=1),
        )

        if not reports:
            logger.debug("Today reports loaded: no reports date=%s", today)
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

        logger.debug("Today reports loaded: count=%s date=%s", len(result), today)
        return result
