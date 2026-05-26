from sqlalchemy.ext.asyncio import AsyncSession
from utils.enums import UserRole
from db.models import User
from repositories.operation_repository import OperationRepository
from repositories.report_repository import ReportRepository
from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository
from utils.apptime import apptime
from utils.logger import get_logger


logger = get_logger(__name__)


class WorkerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.session_repo = SessionRepository(session)
        self.operation_repo = OperationRepository(session)
        self.report_repo = ReportRepository(session)

    async def user_exists(self, telegram_id: int) -> bool:
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        return user is not None

    async def is_admin(self, telegram_id: int) -> bool:
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        return user is not None and user.role == UserRole.ADMIN

    async def get_all_usernames(self) -> list[str]:
        users = await self.user_repo.get_all()
        return [user.username for user in users]

    async def get_or_create_worker(self, username: str) -> None | User:
        username = username.lstrip("@")
        logger.info("Get or create worker requested: username=%s", username)
        user = await self.user_repo.get_by_username(username)
        if user and user.role == UserRole.WORKER:
            logger.debug("Worker already exists: user_id=%s username=%s", user.id, username)
            return user
        elif user and user.role != UserRole.WORKER:
            logger.warning("Get or create worker failed: username=%s exists with role=%s", username, user.role.value)
            return None
        worker = await self.user_repo.create(username,
                                       UserRole.WORKER,
                                       apptime(),
                                       authorised_at=None,
                                       telegram_id=None)
        await self.session.commit()
        logger.info("Worker created: user_id=%s username=%s", worker.id, username)
        return worker


    async def authorize_worker(self, username: str, telegram_id: int) -> None | User:
        username = username.lstrip("@")
        logger.info("Authorize worker requested: username=%s telegram_id=%s", username, telegram_id)
        user = await self.user_repo.get_by_username(username)
        if not user or user.role != UserRole.WORKER:
            logger.warning("Authorize worker failed: username=%s not found as worker", username)
            return None
        user = await self.user_repo.authorize_user(user, telegram_id, apptime())
        await self.session.commit()
        logger.info("Worker authorized: user_id=%s telegram_id=%s", user.id, telegram_id)
        return user

    async def delete_worker(self, username: str) -> None | User:
        username = username.lstrip("@")
        logger.info("Delete worker requested: username=%s", username)
        user = await self.user_repo.get_by_username(username)
        if not user or user.role != UserRole.WORKER:
            logger.warning("Delete worker failed: username=%s not found as worker", username)
            return None
        await self.user_repo.delete(user)
        await self.session.commit()
        logger.info("Worker deleted: user_id=%s username=%s", user.id, username)
        return user

    async def get_last_reports_with_operations(self, telegram_id: int) -> list[dict] | None:
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user or user.role != UserRole.WORKER:
            logger.warning("Get last reports failed: telegram_id=%s is not worker", telegram_id)
            return None

        sessions = await self.session_repo.get_worker_sessions(user.id)
        last_sessions = sessions[:5]
        result: list[dict] = []

        for work_session in last_sessions:

            report = await self.report_repo.get_by_session_id(work_session.id)
            operations = []
            if report is not None:
                operations = await self.operation_repo.get_operations_by_report(report.id)
            if work_session.ended_at:
                duration = (work_session.ended_at - work_session.started_at).total_seconds()
            else:
                duration = None
            result.append(
                {
                    "duration": duration,
                    "report": report,
                    "operations": operations,
                }
            )

        logger.debug("Last reports loaded: user_id=%s sessions=%s", user.id, len(result))
        return result
