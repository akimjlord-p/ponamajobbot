from sqlalchemy.ext.asyncio import AsyncSession
from db.enums import UserRole
from db.models import User
from repositories.operation_repository import OperationRepository
from repositories.report_repository import ReportRepository
from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository
from utils.apptime import apptime


class WorkerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.session_repo = SessionRepository(session)
        self.operation_repo = OperationRepository(session)
        self.report_repo = ReportRepository(session)

    async def get_or_create_worker(self, username: str) -> None | User:
        user = await self.user_repo.get_by_username(username)
        if user and user.role == UserRole.WORKER:
            return user
        elif user and user.role != UserRole.WORKER:
            return None
        worker = await self.user_repo.create(username,
                                       UserRole.WORKER,
                                       apptime(),
                                       authorised_at=None,
                                       telegram_id=None)
        await self.session.commit()
        return worker


    async def authorize_worker(self, username: str, telegram_id: int) -> None | User:
        user = await self.user_repo.get_by_username(username)
        if not user or user.role != UserRole.WORKER:
            return None
        user = await self.user_repo.authorize_user(user, telegram_id, apptime())
        await self.session.commit()
        return user

    async def delete_worker(self, username: str) -> None | User:
        user = await self.user_repo.get_by_username(username)
        if not user or user.role != UserRole.WORKER:
            return None
        await self.user_repo.delete(user)
        await self.session.commit()
        return user

    async def get_last_reports_with_operations(self, telegram_id: int) -> list[dict] | None:
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user or user.role != UserRole.WORKER:
            return None

        sessions = await self.session_repo.get_worker_sessions(user.id)
        last_sessions = sessions[:5]
        result: list[dict] = []

        for work_session in last_sessions:

            report = await self.report_repo.get_by_session_id(work_session.id)
            operations = []
            if report is not None:
                operations = await self.operation_repo.get_operations_by_report(report.id)

            result.append(
                {
                    "duration": (work_session.ended_at - work_session.started_at).total_seconds(),
                    "report": report,
                    "operations": operations,
                }
            )

        return result


