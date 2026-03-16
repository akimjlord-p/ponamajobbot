from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import WorkSession
from db.enums import SessionStatus


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, session_id: int) -> WorkSession | None:
        stmt = select(WorkSession).where(WorkSession.id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_open_session_by_worker(self, worker_id: int) -> WorkSession | None:
        stmt = select(WorkSession).where(
            WorkSession.worker_id == worker_id,
            WorkSession.status == SessionStatus.OPEN,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_worker_sessions(self, worker_id: int) -> list[WorkSession]:
        stmt = (
            select(WorkSession)
            .where(WorkSession.worker_id == worker_id)
            .order_by(WorkSession.started_at.desc())
        )
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