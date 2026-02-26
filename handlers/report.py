import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db import add_report_to_db, get_worker_id_by_username, start_work_session, close_work_session
from models import ReportBase, WorkSession
from keyboards import get_kb
from aiogram.types import ReplyKeyboardRemove
from datetime import datetime
from zoneinfo import ZoneInfo



router = Router()


class AddReportFSM(StatesGroup):
    report = State()

@router.message(F.text.lower() == "/checkin")
async def checkin(message: types.Message):
    logging.info(f"Checkin {message.from_user.username}")
    worker_id = get_worker_id_by_username(username=message.from_user.username)
    work_session = WorkSession(checkin=datetime.now(ZoneInfo("Europe/Moscow")), worker_id=worker_id)
    if start_work_session(work_session):
        await message.answer(text="Вы успешно начали рабочую сессию, не забудьте отметиться в конце /checkout")
    else:
        await message.answer(text="Ваша рабочая сессия уже открыта. /checkout для закрытия сессии")


@router.message(F.text.lower() == "/checkout")
async def checkout(message: types.Message, state: FSMContext):
    logging.info(f"Checkout {message.from_user.username}")
    worker_id = get_worker_id_by_username(username=message.from_user.username)
    res = close_work_session(worker_id=worker_id, checkout_time=datetime.now(ZoneInfo("Europe/Moscow")))
    if not res:
        await message.answer(text="Ваша рабочая сессия не была открыта. /checkin для открытия сессии")
        return

    await state.set_state(AddReportFSM.report)
    await message.answer(text="Вы успешно завершили рабочую смену. Введите текст отчета", reply_markup=ReplyKeyboardRemove())


@router.message(AddReportFSM.report)
async def get_report(message: types.Message, state: FSMContext, is_admin: bool):

    report_text = message.text
    worker_id = get_worker_id_by_username(message.from_user.username)
    moscow_now = datetime.now(ZoneInfo("Europe/Moscow"))
    report = ReportBase(message=report_text, worker_id=worker_id, date=moscow_now)
    add_report_to_db(report)
    await message.answer(text="Ваш отчет успешно сохранён", reply_markup=get_kb(is_admin))
    logging.info(f"Worker {message.from_user.username} get report successfully")
    await state.clear()


