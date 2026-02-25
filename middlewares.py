from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
import logging
from db import get_user_by_username
from config import ADMINS
class AccessMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:

        if isinstance(event, Message):
            username = event.from_user.username
            if not username:
                logging.error(f"User {event.from_user.id} has no username")
                await event.answer(text="Привет, я тебя не узнаю (вероятно скрыт @username ⚠️)")
                return None

            user = get_user_by_username(username)
            if user:
                logging.info(f"User {username} found successfully")
                return await handler(event, data)
            else:
                logging.warning(f"User {username} not found in DB")
                await event.answer(text="Привет, я тебя не узнаю 🤷")
                return None


class AdminMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data:Dict[str, Any]
    ) -> Any:

        if isinstance(event, Message):
            if str(event.from_user.id) in ADMINS:
                logging.info(f"Admin {event.from_user.id} found successfully")
                data['is_admin'] = True
            else:
                logging.info(f"User {event.from_user.id} not found in ADMINS")
                data['is_admin'] = False
            return await handler(event, data)

