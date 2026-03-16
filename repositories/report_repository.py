from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import WorkReport
from db.enums import ReportStatus


class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, report_id: int) -> WorkReport | None:
        stmt = select(WorkReport).where(WorkReport.id == report_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_session_id(self, session_id: int) -> WorkReport | None:
        stmt = select(WorkReport).where(WorkReport.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_reports_for_admin_review(self) -> list[WorkReport]:
        stmt = select(WorkReport).where(
            WorkReport.status.in_(
                [
                    ReportStatus.SHOULD_BE_SENT_TO_ADMIN,
                    ReportStatus.SENT_TO_ADMIN,
                ]
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_worker_reports(self, worker_id: int) -> list[WorkReport]:
        stmt = (
            select(WorkReport)
            .where(WorkReport.worker_id == worker_id)
            .order_by(WorkReport.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        session_id: int,
        worker_id: int,
        text: str,
        status: ReportStatus,
        created_at: datetime,
    ) -> WorkReport:
        report = WorkReport(
            session_id=session_id,
            worker_id=worker_id,
            text=text,
            status=status,
            created_at=created_at,
        )
        self.session.add(report)
        await self.session.flush()
        return report

    async def update_status(
        self,
        report_id: int,
        status: ReportStatus,
        admin_review_comment: str | None = None,
    ) -> WorkReport | None:
        report = await self.get_by_id(report_id)
        if not report:
            return None

        report.status = status
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
    ) -> WorkReport | None:
        report = await self.get_by_id(report_id)
        if not report:
            return None

        report.status = ReportStatus.REVIEWED_BY_ADMIN
        report.reviewed_by_admin_id = reviewed_by_admin_id
        report.reviewed_at = reviewed_at
        if admin_review_comment is not None:
            report.admin_review_comment = admin_review_comment

        await self.session.flush()
        return report

    async def set_total_amount(self, report_id: int, total_amount) -> WorkReport | None:
        report = await self.get_by_id(report_id)
        if not report:
            return None

        report.total_amount = total_amount
        await self.session.flush()
        return report