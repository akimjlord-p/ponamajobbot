from aiogram import Router, types
from aiogram.filters import CommandStart
from keyboards import get_kb
import logging
router = Router()




@router.message(CommandStart())
async def start_command(message: types.Message, is_admin: bool):
    logging.info(f"Starting {message.from_user.username}")
    username = message.from_user.username
    if not is_admin:
        await message.answer(text=f"Привет, {username}!\nКоманды: /report", reply_markup=get_kb(is_admin))
    else:
        await message.answer(text=f"Привет, {username}!\nКоманды: /worker", reply_markup=get_kb(is_admin))
