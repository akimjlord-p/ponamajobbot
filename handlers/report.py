import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db import add_report_to_db, get_worker_id_by_username, start_work_session, close_work_session, \
    get_week_report_by_username, add_week_report, get_open_session
from models import ReportBase, WorkSession, WeekReportBase
from keyboards import get_kb
from aiogram.types import ReplyKeyboardRemove
from datetime import datetime
from zoneinfo import ZoneInfo



router = Router()


class AddReportFSM(StatesGroup):
    report = State()

class AddWeekReportFSM(StatesGroup):
    week_report = State()

@router.message(F.text.lower() == "/checkin")
async def checkin(message: types.Message):
    logging.info(f"Checkin {message.from_user.username}")
    worker_id = get_worker_id_by_username(username=message.from_user.username)
    work_session = WorkSession(check_in=datetime.now(ZoneInfo("Europe/Moscow")), worker_id=worker_id)
    if start_work_session(work_session):
        await message.answer(text="Вы успешно начали рабочую сессию, не забудьте отметиться в конце /checkout")
    else:
        await message.answer(text="Ваша рабочая сессия уже открыта. /checkout для закрытия сессии")


@router.message(F.text.lower() == "/checkout")
async def checkout(message: types.Message, state: FSMContext):
    worker_id = get_worker_id_by_username(username=message.from_user.username)
    res = get_open_session(worker_id=worker_id)
    if not res:
        await message.answer(text="Ваша рабочая сессия не была открыта. /checkin для открытия сессии")
        return

    await state.set_state(AddReportFSM.report)
    await message.answer(text="Введите текст отчета", reply_markup=ReplyKeyboardRemove())



@router.message(AddReportFSM.report)
async def get_report(message: types.Message, state: FSMContext, is_admin: bool):
    report_text = message.text
    worker_id = get_worker_id_by_username(message.from_user.username)
    moscow_now = datetime.now(ZoneInfo("Europe/Moscow"))

    report = ReportBase(message=report_text, worker_id=worker_id, date=moscow_now)
    add_report_to_db(report)

    logging.info(f"Worker {message.from_user.username} send report successfully")

    close_work_session(worker_id=worker_id, checkout_time=moscow_now, report_id=report.id)

    logging.info(f"Checkout {message.from_user.username}")

    await message.answer(text="Ваш отчет успешно сохранён")
    await message.answer(text="Вы успешно завершили рабочую смену", reply_markup=get_kb(is_admin))

    await state.clear()


@router.message(F.text.lower() == "/report")
async def start_week_report(message: types.Message, state: FSMContext):
    res = get_week_report_by_username(username=message.from_user.username)
    if res:
        await message.answer(text="Вы уже отправляли недельный отчет")
        return

    await state.set_state(AddWeekReportFSM.week_report)
    await message.answer(text="Введите текст недельного отчета", reply_markup=ReplyKeyboardRemove())
    logging.info(f"Week report {message.from_user.username}")


@router.message(AddWeekReportFSM.week_report)
async def get_week_report(message: types.Message, state: FSMContext, is_admin: bool):
    report_text = message.text
    week_report = WeekReportBase(message=report_text,
                                 worker_id=get_worker_id_by_username(username=message.from_user.username))
    add_week_report(week_report)
    await message.answer(text="Ваш отчет успешно сохранён", reply_markup=get_kb(is_admin))
    logging.info(f"Worker {message.from_user.username} send report successfully")
    await state.clear()



