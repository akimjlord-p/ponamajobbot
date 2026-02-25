import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db import get_user_by_username, add_report_to_db
from models import ReportBase
from keyboards import get_kb

router = Router()

class ReportFSM(StatesGroup):
    report = State()

@router.message(F.text.lower() == "/report")
async def start_report(message: types.Message, state: FSMContext):
    logging.info(f"User {message.from_user.username} start report successfully")
    await state.set_state(ReportFSM.report)
    await message.answer(text="Привет, введи текст отчета")


@router.message(ReportFSM.report)
async def get_report(message: types.Message, state: FSMContext, is_admin: bool):
    data = await state.get_data()
    report_text = data.get("report")
    report = ReportBase(message=report_text, user_id=message.from_user.id)
    add_report_to_db(report)
    await message.answer(text="Ваш отчет успешно сохранён", reply_markup=get_kb(is_admin))
    logging.info(f"User {message.from_user.username} get report successfully")
    await state.clear()


