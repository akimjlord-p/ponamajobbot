from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.enums import UserRole
from db.models import User


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

    async def get_authorized_workers(self) -> list[User]:
        stmt = select(User).where(
            User.role == UserRole.WORKER,
            User.telegram_id.is_not(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        username: str,
        role: UserRole,
        created_at: datetime,
        telegram_id: int | None = None,
        authorised_at: datetime | None = None,
    ) -> User:
        user = User(
            username=username,
            telegram_id=telegram_id,
            role=role,
            authorised_at=authorised_at,
            created_at=created_at,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(
        self,
        user: User,
        *,
        username: str | None = None,
        telegram_id: int | None = None,
        role: UserRole | None = None,
        authorised_at: datetime | None = None,
    ) -> User:
        if username is not None:
            user.username = username
        if telegram_id is not None:
            user.telegram_id = telegram_id
        if role is not None:
            user.role = role
        if authorised_at is not None:
            user.authorised_at = authorised_at

        await self.session.flush()
        return user

    async def authorize_user(
        self,
        user: User,
        telegram_id: int,
        authorised_at: datetime,
    ) -> User:
        user.telegram_id = telegram_id
        user.authorised_at = authorised_at

        await self.session.flush()
        return user

    async def deauthorize_user(self, user: User) -> User:
        user.telegram_id = None
        user.authorised_at = None

        await self.session.flush()
        return user

    async def delete_by_id(self, user_id: int) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.session.delete(user)
        await self.session.flush()
        return True

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()
