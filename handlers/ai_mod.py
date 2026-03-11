import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import get_kb, ai_kb
from ai_connection import ask_sql

router = Router()


class AiModFSM(StatesGroup):
    question = State()


@router.message(F.text.lower() == '/ai')
async def add_worker(message: types.Message, state: FSMContext):
    logging.info(f"Admin {message.from_user.username} start ai mod")
    await state.set_state(AiModFSM.question)
    await message.answer(text="Привет, введи твой запрос по базе отчетов", reply_markup=ai_kb)


@router.message(AiModFSM.question)
async def add_worker(message: types.Message, state: FSMContext, is_admin: bool):
    if message.text == 'отмена':
        await state.clear()
        await message.answer(text="Вы вышли из ai мода", reply_markup=get_kb(is_admin))
    await message.answer(text='Ожидайте ответа ⏳')
    res = await ask_sql(str(message.text))
    await message.answer(text=res)
    await message.answer(text='Введи твой запрос по базе отчетов')
    logging.info(f"Admin {message.from_user.username} successfully get response from ai")

