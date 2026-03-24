from aiogram.enums import ParseMode
from aiogram import Router, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from keyboards import worker_chapter_kb
from services.worker_service import WorkerService
from db.session import SessionLocal

router = Router()

class WorkerFSM(StatesGroup):
    command = State()

class AddWorkerFSM(StatesGroup):
    username = State()

class DeleteWorkerFSM(StatesGroup):
    username = State()

async def send_worker_menu(message: types.Message, state: FSMContext):
    firstname = message.from_user.first_name or ""
    text = f"""
Привет, <b>администратор {firstname}</b>.
<i>Основные команды этого раздела:</i>
-/список - список сотрудников
-/добавить - добавить сотрудника
-/удалить - удалить сотрудника
"""
    await state.set_state(WorkerFSM.command)
    await message.answer(text, reply_markup=worker_chapter_kb, parse_mode=ParseMode.HTML)


@router.message("/воркер")
async def worker(message: types.Message, state: FSMContext, is_admin: bool):
    if not is_admin:
        return
    await send_worker_menu(message, state)


@router.message("/добавить", WorkerFSM.command)
async def add_worker(message: types.Message, state: FSMContext):
    await state.set_state(AddWorkerFSM.username)
    text = "Введите юзернейм сотрудника. Пример: @username"
    await message.answer(text)


@router.message(AddWorkerFSM.username)
async def get_worker_username_to_add(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        worker_service = WorkerService(session)
        await worker_service.get_or_create_worker(message.text)

        text = f"""Сотрудник {message.text} зарегистрирован в базе"""
        await message.answer(text)

        await send_worker_menu(message, state)


@router.message("/удалить", WorkerFSM.command)
async def delete_worker(message: types.Message, state: FSMContext):
    await state.set_state(DeleteWorkerFSM.username)
    text = "Введите юзернейм сотрудника. Пример: @username"
    await message.answer(text)


@router.message(DeleteWorkerFSM.username)
async def get_worker_username_to_delete(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        worker_service = WorkerService(session)
        result = await worker_service.delete_worker(message.text)
        if result:
            text = f"""Сотрудник {message.text} удален из базы"""

        else:
            text = f"""Сотрудник {message.text} не найден в базе"""
        await message.answer(text)
        await send_worker_menu(message, state)


@router.message("/список", WorkerFSM.command)
async def get_workers(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        worker_service = WorkerService(session)
        workers = await worker_service.get_all_usernames()
        text = "Список сотрудников:\n" + '\n'.join(workers)
        await message.answer(text)
        await send_worker_menu(message, state)

