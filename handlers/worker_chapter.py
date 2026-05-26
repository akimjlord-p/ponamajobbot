from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from db.session import SessionLocal
from handlers.start import send_start_menu
from services.ai_service.container import ai_service_mini
from services.comment_service import CommentService
from services.report_service import ReportService
from services.session_service import SessionService
from utils.enums import WorkerCommentTag

router = Router()


COMMENT_TAG_LABELS: dict[str, WorkerCommentTag] = {
    "Идея": WorkerCommentTag.IDEA,
    "Жалоба": WorkerCommentTag.COMPLAINT,
    "Другое": WorkerCommentTag.OTHER,
    "Idea": WorkerCommentTag.IDEA,
    "Complaint": WorkerCommentTag.COMPLAINT,
    "Other": WorkerCommentTag.OTHER,
    "idea": WorkerCommentTag.IDEA,
    "complaint": WorkerCommentTag.COMPLAINT,
    "other": WorkerCommentTag.OTHER,
}

comment_tag_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Idea"),
            KeyboardButton(text="Complaint"),
            KeyboardButton(text="Other"),
        ],
        [KeyboardButton(text="/back")],
    ],
    resize_keyboard=True,
)


class CheckoutFSM(StatesGroup):
    report_text = State()


class CommentFSM(StatesGroup):
    tag = State()
    text = State()


@router.message(F.text.lower() == "/back", CheckoutFSM.report_text)
@router.message(F.text.lower() == "/back", CommentFSM.tag)
@router.message(F.text.lower() == "/back", CommentFSM.text)
async def back_to_start(message: types.Message, state: FSMContext, is_admin: bool):
    await state.clear()
    await send_start_menu(message, state, is_admin)


@router.message(F.text.lower() == "/checkin")
async def checkin(message: types.Message, state: FSMContext, is_admin: bool):
    await state.clear()
    telegram_id = message.from_user.id
    async with SessionLocal() as session:
        session_service = SessionService(session)
        work_session = await session_service.open_session(telegram_id)

    if work_session is None:
        await message.answer("Не удалось открыть смену. Возможно, смена уже открыта.")
        return

    await message.answer(f"Смена открыта: {work_session.started_at.strftime('%H:%M')}.")


@router.message(F.text.lower() == "/checkout")
async def checkout_start(message: types.Message, state: FSMContext, is_admin: bool):
    telegram_id = message.from_user.id
    async with SessionLocal() as session:
        session_service = SessionService(session)
        open_session = await session_service.get_open_session(telegram_id)

    if open_session is None:
        await message.answer("Открытая смена не найдена. Сначала используйте /checkin.")
        return

    await state.update_data(session_id=open_session.id)
    await state.set_state(CheckoutFSM.report_text)
    await message.answer("Введите отчет по смене одним сообщением.")


@router.message(CheckoutFSM.report_text)
async def checkout_finish(message: types.Message, state: FSMContext, is_admin: bool):
    report_text = (message.text or "").strip()
    if not report_text:
        await message.answer("Отчет не должен быть пустым.")
        return

    data = await state.get_data()
    session_id = data.get("session_id")
    if not session_id:
        await state.clear()
        await message.answer("Не удалось определить рабочую сессию. Запустите /checkout заново.")
        return

    telegram_id = message.from_user.id
    async with SessionLocal() as session:
        report_service = ReportService(session, ai_service_mini)
        session_service = SessionService(session)

        report = await report_service.create_work_report(report_text, telegram_id, session_id)
        work_session = await session_service.close_session(telegram_id)

    await state.clear()

    if report is None or work_session is None:
        await message.answer("Не удалось завершить смену. Попробуйте еще раз.")
        return

    await message.answer("Отчет успешно создан.")
    await send_start_menu(message, state, is_admin)


@router.message(F.text.lower() == "/comment")
async def comment_start(message: types.Message, state: FSMContext, is_admin: bool):
    await state.set_state(CommentFSM.tag)
    await message.answer("Выберите тип комментария.", reply_markup=comment_tag_kb)


@router.message(CommentFSM.tag)
async def comment_get_tag(message: types.Message, state: FSMContext):
    raw_tag = (message.text or "").strip()
    tag = COMMENT_TAG_LABELS.get(raw_tag)
    if tag is None:
        await message.answer("Выберите тип комментария кнопкой: Idea, Complaint или Other.")
        return

    await state.update_data(tag=tag.value)
    await state.set_state(CommentFSM.text)
    await message.answer("Введите текст комментария.")


@router.message(CommentFSM.text)
async def comment_save(message: types.Message, state: FSMContext, is_admin: bool):
    comment_text = (message.text or "").strip()
    if not comment_text:
        await message.answer("Комментарий не должен быть пустым.")
        return

    data = await state.get_data()
    tag_value = data.get("tag")
    if not tag_value:
        await state.clear()
        await message.answer("Не удалось определить тип комментария. Запустите /comment заново.")
        return

    async with SessionLocal() as session:
        comment_service = CommentService(session)
        comment = await comment_service.create(
            telegram_id=message.from_user.id,
            comment_text=comment_text,
            tag=WorkerCommentTag(tag_value),
        )

    await state.clear()

    if comment is None:
        await message.answer("Не удалось сохранить комментарий.")
        return

    await message.answer("Комментарий сохранен.")
    await send_start_menu(message, state, is_admin)
