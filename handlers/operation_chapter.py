from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from db.session import SessionLocal
from keyboards import operation_chapter_kb
from services.ai_service.container import ai_service_mini
from services.operation_type_service import OperationTypeService

router = Router()

SKIP_SYNONYM_TEXT = "Пропустить"
skip_synonym_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=SKIP_SYNONYM_TEXT)]],
    resize_keyboard=True,
)


class OperationFSM(StatesGroup):
    command = State()


class AddOperationFSM(StatesGroup):
    name = State()
    manual_synonyms = State()


async def send_operation_menu(message: types.Message, state: FSMContext):
    firstname = message.from_user.first_name or ""
    text = f"""
Привет, <b>администратор {firstname}</b>.
<i>Основные команды этого раздела:</i>
-/список - список операций
-/добавить - добавить операцию
"""
    await state.set_state(OperationFSM.command)
    await message.answer(text, reply_markup=operation_chapter_kb, parse_mode=ParseMode.HTML)


@router.message("/операции")
async def operation(message: types.Message, state: FSMContext, is_admin: bool):
    if not is_admin:
        return
    await send_operation_menu(message, state)


@router.message("/добавить", OperationFSM.command)
async def add_operation(message: types.Message, state: FSMContext):
    await state.set_state(AddOperationFSM.name)
    await message.answer("Введите название операции.")


@router.message(AddOperationFSM.name)
async def get_operation_name_to_add(message: types.Message, state: FSMContext):
    operation_name = message.text.strip()

    async with SessionLocal() as session:
        operation_service = OperationTypeService(session)
        operation_type = await operation_service.add_operation_type(operation_name)

        if operation_type is None:
            await message.answer(f"Операция {operation_name} уже есть в базе")
            await send_operation_menu(message, state)
            return

        generated_synonyms = await ai_service_mini.generate_synonyms(operation_name) or []
        added_synonyms = await operation_service.add_operation_type_synonyms(
            operation_type,
            generated_synonyms,
        )

    await state.update_data(operation_name=operation_name)
    await state.set_state(AddOperationFSM.manual_synonyms)

    if added_synonyms:
        synonyms_text = "\n".join(f"- {synonym.synonym}" for synonym in added_synonyms)
        text = (
            f"Операция {operation_name} зарегистрирована в базе.\n"
            f"ИИ предложил и добавил синонимы:\n{synonyms_text}\n\n"
            "Можете отправить дополнительный синоним сообщением или нажать кнопку 'Пропустить'."
        )
    else:
        text = (
            f"Операция {operation_name} зарегистрирована в базе.\n"
            "ИИ не предложил новых синонимов.\n\n"
            "Можете отправить дополнительный синоним сообщением или нажать кнопку 'Пропустить'."
        )

    await message.answer(text, reply_markup=skip_synonym_kb)


@router.message(AddOperationFSM.manual_synonyms)
async def get_manual_operation_synonyms(message: types.Message, state: FSMContext):
    if message.text.strip() == SKIP_SYNONYM_TEXT:
        await send_operation_menu(message, state)
        return

    data = await state.get_data()
    operation_name = data["operation_name"]
    synonym = message.text.strip()

    async with SessionLocal() as session:
        operation_service = OperationTypeService(session)
        operation_type = await operation_service.get_operation_type_by_name(operation_name)

        if operation_type is None:
            await message.answer(f"Операция {operation_name} не найдена в базе")
            await send_operation_menu(message, state)
            return

        added_synonyms = await operation_service.add_operation_type_synonyms(
            operation_type,
            [synonym],
        )

    if added_synonyms:
        text = (
            f"Для операции {operation_name} добавлен синоним: {added_synonyms[0].synonym}\n"
            "Можете отправить еще один дополнительный синоним или нажать 'Пропустить'."
        )
    else:
        text = (
            f"Синоним '{synonym}' не был добавлен для операции {operation_name}\n"
            "Возможно, он уже существует. Можете отправить другой синоним или нажать 'Пропустить'."
        )

    await message.answer(text, reply_markup=skip_synonym_kb)


@router.message("/список", OperationFSM.command)
async def get_operations(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        operation_service = OperationTypeService(session)
        operations = await operation_service.get_all_operation_types()

    if operations:
        text = "Список операций:\n" + "\n".join(operation.name for operation in operations)
    else:
        text = "Список операций пуст"

    await message.answer(text)
    await send_operation_menu(message, state)
