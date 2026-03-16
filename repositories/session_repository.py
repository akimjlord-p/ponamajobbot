from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.enums import SessionStatus
from db.models import WorkSession


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, session_id: int) -> WorkSession | None:
        stmt = self._base_query().where(WorkSession.id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_open_session_by_worker(self, worker_id: int) -> WorkSession | None:
        stmt = self._base_query().where(
            WorkSession.worker_id == worker_id,
            WorkSession.status == SessionStatus.OPEN,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_worker_sessions(self, worker_id: int) -> list[WorkSession]:
        stmt = (
            self._base_query()
            .where(WorkSession.worker_id == worker_id)
            .order_by(WorkSession.started_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_worker_and_date(
        self,
        worker_id: int,
        work_date: date,
    ) -> WorkSession | None:
        stmt = self._base_query().where(
            WorkSession.worker_id == worker_id,
            WorkSession.work_date == work_date,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_sessions_in_range(
        self,
        date_from: date,
        date_to: date,
        *,
        worker_id: int | None = None,
        status: SessionStatus | None = None,
    ) -> list[WorkSession]:
        stmt = self._base_query().where(
            WorkSession.work_date >= date_from,
            WorkSession.work_date <= date_to,
        )
        if worker_id is not None:
            stmt = stmt.where(WorkSession.worker_id == worker_id)
        if status is not None:
            stmt = stmt.where(WorkSession.status == status)

        stmt = stmt.order_by(WorkSession.work_date.desc(), WorkSession.started_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        worker_id: int,
        work_date: date,
        started_at: datetime,
        created_by_admin_id: int | None = None,
        is_created_by_admin: bool = False,
    ) -> WorkSession:
        work_session = WorkSession(
            worker_id=worker_id,
            created_by_admin_id=created_by_admin_id,
            work_date=work_date,
            started_at=started_at,
            status=SessionStatus.OPEN,
            is_auto_checkout=False,
            is_created_by_admin=is_created_by_admin,
        )
        self.session.add(work_session)
        await self.session.flush()
        return work_session

    async def update(
        self,
        work_session: WorkSession,
        *,
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
        work_date: date | None = None,
        status: SessionStatus | None = None,
        is_auto_checkout: bool | None = None,
        created_by_admin_id: int | None = None,
        is_created_by_admin: bool | None = None,
    ) -> WorkSession:
        if started_at is not None:
            work_session.started_at = started_at
        if ended_at is not None:
            work_session.ended_at = ended_at
        if work_date is not None:
            work_session.work_date = work_date
        if status is not None:
            work_session.status = status
        if is_auto_checkout is not None:
            work_session.is_auto_checkout = is_auto_checkout
        if created_by_admin_id is not None:
            work_session.created_by_admin_id = created_by_admin_id
        if is_created_by_admin is not None:
            work_session.is_created_by_admin = is_created_by_admin

        await self.session.flush()
        return work_session

    async def close(
        self,
        session_id: int,
        ended_at: datetime,
        is_auto_checkout: bool = False,
    ) -> WorkSession | None:
        work_session = await self.get_by_id(session_id)
        if not work_session:
            return None

        work_session.ended_at = ended_at
        work_session.is_auto_checkout = is_auto_checkout
        work_session.status = (
            SessionStatus.AUTO_CLOSED if is_auto_checkout else SessionStatus.CLOSED
        )

        await self.session.flush()
        return work_session

    async def delete(self, work_session: WorkSession) -> None:
        await self.session.delete(work_session)
        await self.session.flush()

    @staticmethod
    def _base_query() -> Select[tuple[WorkSession]]:
        return select(WorkSession).options(selectinload(WorkSession.report))
