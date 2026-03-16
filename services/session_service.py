from sqlalchemy.ext.asyncio import AsyncSession
from db.models import WorkSession
from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository
from utils.apptime import apptime, appdate


class SessionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.session_repository = SessionRepository(session)
        self.user_repository = UserRepository(session)

    async def open_session(self, telegram_id: int) -> None | WorkSession:
        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            return None
        if await self.session_repository.get_open_session_by_worker(user.id):
            return None
        work_session = await self.session_repository.create(user.id, appdate(), apptime())
        await self.session.commit()
        return work_session


    async def close_session(self, telegram_id: int, is_auto_checkout: bool = False) -> None | WorkSession:
        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            return None
        work_session = await self.session_repository.get_open_session_by_worker(user.id)
        work_session = await self.session_repository.close(int(str(work_session.id)), apptime(), is_auto_checkout=is_auto_checkout)
        await self.session.commit()
        return work_session