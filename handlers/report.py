import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db import add_report_to_db, get_worker_id_by_username
from models import ReportBase
from keyboards import get_kb
from aiogram.types import ReplyKeyboardRemove
from datetime import datetime
from zoneinfo import ZoneInfo



router = Router()


class AddReportFSM(StatesGroup):
    report = State()


@router.message(F.text.lower() == "/report")
async def start_report(message: types.Message, state: FSMContext):
    logging.info(f"Worker {message.from_user.username} start report successfully")
    await state.set_state(AddReportFSM.report)
    await message.answer(text="Привет, введи текст отчета", reply_markup=ReplyKeyboardRemove())


@router.message(AddReportFSM.report)
async def get_report(message: types.Message, state: FSMContext, is_admin: bool):

    report_text = message.text
    worker_id = get_worker_id_by_username(message.from_user.username)
    moscow_now = datetime.now(ZoneInfo("Europe/Moscow"))
    report = ReportBase(message=report_text, worker_id=worker_id, date=moscow_now.strftime("%d-%m"))
    add_report_to_db(report)
    await message.answer(text="Ваш отчет успешно сохранён", reply_markup=get_kb(is_admin))
    logging.info(f"Worker {message.from_user.username} get report successfully")
    await state.clear()


