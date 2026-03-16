from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.enums import ReportResultType, ReportStatus
from db.models import WorkReport, WorkSession


class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, report_id: int) -> WorkReport | None:
        stmt = self._base_query().where(WorkReport.id == report_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_session_id(self, session_id: int) -> WorkReport | None:
        stmt = self._base_query().where(WorkReport.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_worker_and_date(
        self,
        worker_id: int,
        target_date: date,
    ) -> list[WorkReport]:
        stmt = (
            self._base_query()
            .join(WorkReport.session)
            .where(
                WorkReport.worker_id == worker_id,
                WorkReport.session.has(work_date=target_date),
            )
            .order_by(WorkReport.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_reports_for_admin_review(self) -> list[WorkReport]:
        stmt = self._base_query().where(
            WorkReport.status.in_([
                ReportStatus.SHOULD_BE_SENT_TO_ADMIN,
                ReportStatus.SENT_TO_ADMIN,
            ])
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_worker_reports(self, worker_id: int) -> list[WorkReport]:
        stmt = (
            self._base_query()
            .where(WorkReport.worker_id == worker_id)
            .order_by(WorkReport.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_reports_in_range(
        self,
        date_from: date,
        date_to: date,
        *,
        worker_id: int | None = None,
        status: ReportStatus | None = None,
    ) -> list[WorkReport]:
        stmt = self._base_query().where(
            WorkReport.session.has(WorkSession.work_date >= date_from),
            WorkReport.session.has(WorkSession.work_date <= date_to),
        )
        if worker_id is not None:
            stmt = stmt.where(WorkReport.worker_id == worker_id)
        if status is not None:
            stmt = stmt.where(WorkReport.status == status)

        stmt = stmt.order_by(WorkReport.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        session_id: int,
        worker_id: int,
        text: str,
        status: ReportStatus,
        created_at: datetime,
        *,
        result_type: ReportResultType | None = None,
        admin_review_comment: str | None = None,
        reviewed_by_admin_id: int | None = None,
        reviewed_at: datetime | None = None,
        total_amount: Decimal | None = None,
    ) -> WorkReport:
        report = WorkReport(
            session_id=session_id,
            worker_id=worker_id,
            text=text,
            status=status,
            result_type=result_type,
            admin_review_comment=admin_review_comment,
            reviewed_by_admin_id=reviewed_by_admin_id,
            reviewed_at=reviewed_at,
            total_amount=total_amount,
            created_at=created_at,
        )
        self.session.add(report)
        await self.session.flush()
        return report

    async def update(
        self,
        report: WorkReport,
        *,
        text: str | None = None,
        status: ReportStatus | None = None,
        result_type: ReportResultType | None = None,
        admin_review_comment: str | None = None,
        reviewed_by_admin_id: int | None = None,
        reviewed_at: datetime | None = None,
        total_amount: Decimal | None = None,
    ) -> WorkReport:
        if text is not None:
            report.text = text
        if status is not None:
            report.status = status
        if result_type is not None:
            report.result_type = result_type
        if admin_review_comment is not None:
            report.admin_review_comment = admin_review_comment
        if reviewed_by_admin_id is not None:
            report.reviewed_by_admin_id = reviewed_by_admin_id
        if reviewed_at is not None:
            report.reviewed_at = reviewed_at
        if total_amount is not None:
            report.total_amount = total_amount

        await self.session.flush()
        return report

    async def update_status(
        self,
        report_id: int,
        status: ReportStatus,
        admin_review_comment: str | None = None,
        result_type: ReportResultType | None = None,
    ) -> WorkReport | None:
        report = await self.get_by_id(report_id)
        if not report:
            return None

        report.status = status
        if result_type is not None:
            report.result_type = result_type
        if admin_review_comment is not None:
            report.admin_review_comment = admin_review_comment

        await self.session.flush()
        return report

    async def set_reviewed(
        self,
        report_id: int,
        reviewed_by_admin_id: int,
        reviewed_at: datetime,
        admin_review_comment: str | None = None,
        result_type: ReportResultType | None = None,
    ) -> WorkReport | None:
        report = await self.get_by_id(report_id)
        if not report:
            return None

        report.status = ReportStatus.REVIEWED_BY_ADMIN
        report.reviewed_by_admin_id = reviewed_by_admin_id
        report.reviewed_at = reviewed_at
        if result_type is not None:
            report.result_type = result_type
        if admin_review_comment is not None:
            report.admin_review_comment = admin_review_comment

        await self.session.flush()
        return report

    async def set_total_amount(
        self,
        report_id: int,
        total_amount: Decimal,
    ) -> WorkReport | None:
        report = await self.get_by_id(report_id)
        if not report:
            return None

        report.total_amount = total_amount
        await self.session.flush()
        return report

    async def delete(self, report: WorkReport) -> None:
        await self.session.delete(report)
        await self.session.flush()

    @staticmethod
    def _base_query() -> Select[tuple[WorkReport]]:
        return select(WorkReport).options(
            selectinload(WorkReport.session),
            selectinload(WorkReport.performed_operations),
        )
