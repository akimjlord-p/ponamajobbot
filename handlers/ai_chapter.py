from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.session import SessionLocal
from handlers.start import send_start_menu
from keyboards import ai_chapter_kb
from repositories.user_repository import UserRepository
from services.ai_service.container import ai_service_smart
from services.context_service import ContextService

router = Router()

TELEGRAM_MESSAGE_LIMIT = 4000


async def answer_long_message(message: types.Message, text: str) -> None:
    chunks: list[str] = []
    current_chunk = ""
    for paragraph in text.split("\n"):
        candidate = paragraph if not current_chunk else f"{current_chunk}\n{paragraph}"
        if len(candidate) <= TELEGRAM_MESSAGE_LIMIT:
            current_chunk = candidate
            continue
        if current_chunk:
            chunks.append(current_chunk)
        while len(paragraph) > TELEGRAM_MESSAGE_LIMIT:
            chunks.append(paragraph[:TELEGRAM_MESSAGE_LIMIT])
            paragraph = paragraph[TELEGRAM_MESSAGE_LIMIT:]
        current_chunk = paragraph
    if current_chunk:
        chunks.append(current_chunk)

    for chunk in chunks:
        await message.answer(chunk)


class AiFSM(StatesGroup):
    command = State()


class QuestionFSM(StatesGroup):
    question = State()


class ContextFSM(StatesGroup):
    context = State()


async def send_ai_menu(message: types.Message, state: FSMContext):
    firstname = message.from_user.first_name or ""
    text = f"""
Привет, <b>администратор {firstname}</b>.
<i>Основные команды этого раздела:</i>
- /question - задать вопрос ИИ
- /context - добавить общий контекст для запросов админа
- /show_context - посмотреть текущий контекст для аналитики
- /back - вернуться в главное меню
"""
    await state.set_state(AiFSM.command)
    await message.answer(text, reply_markup=ai_chapter_kb, parse_mode=ParseMode.HTML)


@router.message(F.text.lower() == "/ai")
async def ai_chapter(message: types.Message, state: FSMContext, is_admin: bool):
    if not is_admin:
        return
    await send_ai_menu(message, state)


@router.message(F.text.lower() == "/back", AiFSM.command)
@router.message(F.text.lower() == "/back", QuestionFSM.question)
@router.message(F.text.lower() == "/back", ContextFSM.context)
async def back_to_start(message: types.Message, state: FSMContext, is_admin: bool):
    await state.clear()
    await send_start_menu(message, state, is_admin)


@router.message(F.text.lower() == "/question", AiFSM.command)
async def question(message: types.Message, state: FSMContext):
    await state.set_state(QuestionFSM.question)
    await message.answer("Введите ваш вопрос. Для выхода в главное меню используйте /back.")


@router.message(QuestionFSM.question)
async def get_question(message: types.Message, state: FSMContext):
    question_text = (message.text or "").strip()
    if not question_text:
        await message.answer("Вопрос не должен быть пустым.")
        return

    async with SessionLocal() as session:
        context_service = ContextService(session)
        contexts = await context_service.get_admin_requests_contexts()
        result = await ai_service_smart.analytic_question(question_text, session, contexts)

    if result is None:
        await message.answer("Произошла ошибка, попробуйте позже.")
        await send_ai_menu(message, state)
        return

    await answer_long_message(message, result.answer)
    await message.answer("Введите следующий вопрос или используйте /back.")


@router.message(F.text.lower() == "/context", AiFSM.command)
async def add_context(message: types.Message, state: FSMContext):
    await state.set_state(ContextFSM.context)
    await message.answer("Введите контекст для запросов админа. Для выхода в главное меню используйте /back.")


@router.message(F.text.lower() == "/show_context", AiFSM.command)
async def show_context(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        context_service = ContextService(session)
        contexts = await context_service.get_admin_requests_contexts()

    if not contexts:
        await message.answer("Контекст для аналитики пока не задан.")
        await send_ai_menu(message, state)
        return

    lines = ["Текущий контекст для аналитики:"]
    for index, context in enumerate(contexts, start=1):
        created_at = context.created_at.strftime("%d.%m.%Y %H:%M") if context.created_at else "без даты"
        lines.append(f"\n{index}. {created_at}\n{context.text.strip()}")

    await answer_long_message(message, "\n".join(lines))
    await send_ai_menu(message, state)


@router.message(ContextFSM.context)
async def save_context(message: types.Message, state: FSMContext):
    context_text = (message.text or "").strip()
    if not context_text:
        await message.answer("Контекст не должен быть пустым.")
        return

    async with SessionLocal() as session:
        user_repository = UserRepository(session)
        admin = await user_repository.get_by_telegram_id(message.from_user.id)
        if admin is None:
            await message.answer("Администратор не найден в базе.")
            await send_ai_menu(message, state)
            return

        context_service = ContextService(session)
        await context_service.add_admin_requests_context(
            text=context_text,
            created_by_admin_id=admin.id,
        )

    await message.answer("Контекст для запросов админа сохранён.")
    await send_ai_menu(message, state)
