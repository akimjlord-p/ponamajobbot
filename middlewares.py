from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from db.session import SessionLocal
from services.worker_service import WorkerService


class UserExistsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        telegram_id = event.from_user.id
        username = event.from_user.username

        async with SessionLocal() as session:
            worker_service = WorkerService(session)

            if await worker_service.user_exists(telegram_id):
                return await handler(event, data)

            if username:
                authorized_user = await worker_service.authorize_worker(
                    username=username,
                    telegram_id=telegram_id,
                )
                if authorized_user is not None:
                    return await handler(event, data)



        await event.answer(text="Привет, я тебя не узнаю 🤷")
        return None


class AdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        async with SessionLocal() as session:
            worker_service = WorkerService(session)
            data["is_admin"] = await worker_service.is_admin(event.from_user.id)

        return await handler(event, data)
