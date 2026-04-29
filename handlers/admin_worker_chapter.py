from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.session import SessionLocal
from handlers.start import send_start_menu
from keyboards import worker_chapter_kb
from services.worker_service import WorkerService

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
- /list - список сотрудников
- /add - добавить сотрудника
- /delete - удалить сотрудника
- /back - вернуться в главное меню
"""
    await state.set_state(WorkerFSM.command)
    await message.answer(text, reply_markup=worker_chapter_kb, parse_mode=ParseMode.HTML)


@router.message(F.text.lower() == "/workers")
async def worker(message: types.Message, state: FSMContext, is_admin: bool):
    if not is_admin:
        return
    await send_worker_menu(message, state)


@router.message(F.text.lower() == "/back", WorkerFSM.command)
@router.message(F.text.lower() == "/back", AddWorkerFSM.username)
@router.message(F.text.lower() == "/back", DeleteWorkerFSM.username)
async def back_to_start(message: types.Message, state: FSMContext, is_admin: bool):
    await state.clear()
    await send_start_menu(message, state, is_admin)


@router.message(F.text.lower() == "/add", WorkerFSM.command)
async def add_worker(message: types.Message, state: FSMContext):
    await state.set_state(AddWorkerFSM.username)
    await message.answer("Введите юзернейм сотрудника. Пример: @username")


@router.message(AddWorkerFSM.username)
async def get_worker_username_to_add(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        worker_service = WorkerService(session)
        await worker_service.get_or_create_worker(message.text)

    await message.answer(f"Сотрудник {message.text} зарегистрирован в базе.")
    await send_worker_menu(message, state)


@router.message(F.text.lower() == "/delete", WorkerFSM.command)
async def delete_worker(message: types.Message, state: FSMContext):
    await state.set_state(DeleteWorkerFSM.username)
    await message.answer("Введите юзернейм сотрудника. Пример: @username")


@router.message(DeleteWorkerFSM.username)
async def get_worker_username_to_delete(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        worker_service = WorkerService(session)
        result = await worker_service.delete_worker(message.text)

    if result:
        text = f"Сотрудник {message.text} удалён из базы."
    else:
        text = f"Сотрудник {message.text} не найден в базе."

    await message.answer(text)
    await send_worker_menu(message, state)


@router.message(F.text.lower() == "/list", WorkerFSM.command)
async def get_workers(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        worker_service = WorkerService(session)
        workers = await worker_service.get_all_usernames()

    text = "Список сотрудников:\n" + "\n".join(workers) if workers else "Список сотрудников пуст."
    await message.answer(text)
    await send_worker_menu(message, state)
