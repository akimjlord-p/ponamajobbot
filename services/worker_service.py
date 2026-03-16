from sqlalchemy.ext.asyncio import AsyncSession
from db.enums import UserRole
from db.models import User
from repositories.user_repository import UserRepository
from utils.apptime import apptime

class WorkerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_or_create_worker(self, username: str) -> None | User:
        user = await self.user_repo.get_by_username(username)
        if user and user.role == UserRole.WORKER:
            return user
        elif user and user.role != UserRole.WORKER:
            return False
        worker = await self.user_repo.create(username,
                                       UserRole.WORKER,
                                       apptime(),
                                       authorised_at=None,
                                       telegram_id=None)
        await self.session.commit()
        return worker


    async def authorise_worker(self, username: str, telegram_id: int) -> None | User:
        user = await self.user_repo.get_by_username(username)
        if not user or user.role != UserRole.WORKER:
            return False
        worker = await self.user_repo.authorize_user(user, telegram_id, apptime())
        await self.session.commit()
        return worker

    async def delete_worker(self, username: str) -> bool:
        user = await self.user_repo.get_by_username(username)
        if not user or user.role != UserRole.WORKER:
            return False
        await self.user_repo.delete(user)
        await self.session.commit()
        return True
