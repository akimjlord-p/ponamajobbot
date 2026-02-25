import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db import add_worker_to_db
from models import WorkerBase
from keyboards import get_kb
from aiogram.types import ReplyKeyboardRemove

router = Router()


class AddWorkerFSM(StatesGroup):
    worker = State()


@router.message(F.text.lower() == '/worker')
async def add_worker(message: types.Message, state: FSMContext):
    logging.info(f"Admin {message.from_user.username} start adding worker successfully")
    await state.set_state(AddWorkerFSM.worker)
    await message.answer(text="Привет, введи ник нового работника в формате: @username", reply_markup=ReplyKeyboardRemove())


@router.message(AddWorkerFSM.worker)
async def add_worker(message: types.Message, state: FSMContext, is_admin: bool):
    username = message.text
    new_worker = WorkerBase(username=username[1:])
    add_worker_to_db(new_worker)
    await state.clear()
    logging.info(f"Admin {message.from_user.username} add worker successfully")
    await message.answer(text=f"Работник {username} успешно добавлен", reply_markup=get_kb(is_admin))

