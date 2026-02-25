import logging
from aiogram import Router, types
from aiogram.filters import CommandStart
from db import get_user_by_username


router = Router()




@router.message(CommandStart())
async def start_command(message: types.Message):
    username = message.from_user.username
    await message.answer(text=f"Привет, {username}!\nКоманды: /report")
