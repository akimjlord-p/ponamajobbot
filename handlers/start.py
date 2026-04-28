from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import logging
import re

from keyboards import get_main_kb

router = Router()


async def send_start_menu(message: types.Message, state: FSMContext, is_admin: bool):
    firstname = message.from_user.first_name or ""
    if is_admin:
        text = f"""
Привет, <b>администратор {firstname}</b>.
<i>Основные команды:</i>
- /воркер - раздел с сотрудниками
- /ии - раздел с ИИ-аналитикой
- /товары - раздел с текущими товарами
- /операции - раздел с текущими операциями
- /тарифы - раздел с текущими тарифами
        """
    else:
        text = f"""
Привет, <b>сотрудник {firstname}</b>.
<i>Основные команды:</i>
- /чекин - открыть смену
- /чекаут - закрыть смену, если она уже открыта
- /комент - оставить дополнительный комментарий
        """
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_kb(is_admin))


@router.message(CommandStart())
async def start(message: types.Message, command: CommandStart, state: FSMContext, is_admin: bool):
    await send_start_menu(message, state, is_admin)
