import logging
from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from db import get_user_by_username


router = Router()


# ==============================
#           FSM
# ==============================

class ReportFSM(StatesGroup):
    report = State()

@router.message(CommandStart())  # Не забывайте скобки в CommandStart()
async def start_command(message: types.Message):
    username = message.from_user.username

    if not username:
        logging.error(f"User {message.from_user.id} has no username")
        await message.answer(text="Привет, я тебя не узнаю (скрыт @username ⚠️)")
        return

    user = get_user_by_username(username)

    if user:
        logging.info(f"User {username} found successfully")
        await message.answer(text=f"Привет, {username}!\nКоманды: /report")
    else:
        logging.warning(f"User {username} not found in DB")
        await message.answer(text="Привет, я тебя не узнаю 🤷")