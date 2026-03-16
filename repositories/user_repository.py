from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from db.enums import UserRole


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_admins(self) -> list[User]:
        stmt = select(User).where(User.role == UserRole.ADMIN)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_workers(self) -> list[User]:
        stmt = select(User).where(User.role == UserRole.WORKER)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        username: str,
        role: UserRole,
        authorised_at,
        telegram_id: int | None = None,
    ) -> User:
        user = User(
            username=username,
            telegram_id=telegram_id,
            role=role,
            authorised_at=authorised_at,
        )
        self.session.add(user)
        await self.session.flush()
        return user