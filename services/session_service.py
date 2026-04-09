from sqlalchemy.ext.asyncio import AsyncSession
from db.models import WorkSession
from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository
from utils.apptime import apptime, appdate
from utils.logger import get_logger


logger = get_logger(__name__)


class SessionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.session_repository = SessionRepository(session)
        self.user_repository = UserRepository(session)

    async def open_session(self, telegram_id: int) -> None | WorkSession:
        logger.info("Open session requested: telegram_id=%s", telegram_id)
        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            logger.warning("Open session failed: user not found telegram_id=%s", telegram_id)
            return None
        if await self.session_repository.get_open_session_by_worker(user.id):
            logger.warning("Open session skipped: active session already exists user_id=%s", user.id)
            return None
        work_session = await self.session_repository.create(user.id, appdate(), apptime())
        await self.session.commit()
        logger.info("Session opened: session_id=%s user_id=%s", work_session.id, user.id)
        return work_session

    async def get_open_session(self, telegram_id: int) -> None | WorkSession:
        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            logger.debug("Get open session: user not found telegram_id=%s", telegram_id)
            return None
        work_session = await self.session_repository.get_open_session_by_worker(user.id)
        if work_session is None:
            logger.debug("Get open session: no active session user_id=%s", user.id)
        return work_session

    async def close_session(self, telegram_id: int, is_auto_checkout: bool = False) -> None | WorkSession:
        logger.info(
            "Close session requested: telegram_id=%s is_auto_checkout=%s",
            telegram_id,
            is_auto_checkout,
        )
        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            logger.warning("Close session failed: user not found telegram_id=%s", telegram_id)
            return None
        work_session = await self.session_repository.get_open_session_by_worker(user.id)
        if work_session is None:
            logger.warning("Close session failed: no open session user_id=%s", user.id)
            return None
        work_session = await self.session_repository.close(work_session.id, apptime(), is_auto_checkout=is_auto_checkout)
        await self.session.commit()
        logger.info("Session closed: session_id=%s user_id=%s", work_session.id, user.id)
        return work_session
