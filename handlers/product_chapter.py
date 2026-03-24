from aiogram import Router, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from db.session import SessionLocal
from keyboards import product_chapter_kb
from services.ai_service.container import ai_service_mini
from services.product_service import ProductService

router = Router()

SKIP_SYNONYM_TEXT = "Пропустить"
skip_synonym_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=SKIP_SYNONYM_TEXT)]],
    resize_keyboard=True,
)


class ProductFSM(StatesGroup):
    command = State()


class AddProductFSM(StatesGroup):
    name = State()
    manual_synonyms = State()


async def send_product_menu(message: types.Message, state: FSMContext):
    firstname = message.from_user.first_name or ""
    text = f"""
Привет, <b>администратор {firstname}</b>.
<i>Основные команды этого раздела:</i>
-/список - список товаров
-/добавить - добавить товар
"""
    await state.set_state(ProductFSM.command)
    await message.answer(text, reply_markup=product_chapter_kb, parse_mode=ParseMode.HTML)


@router.message("/товары")
async def product(message: types.Message, state: FSMContext, is_admin: bool):
    if not is_admin:
        return
    await send_product_menu(message, state)


@router.message("/добавить", ProductFSM.command)
async def add_product(message: types.Message, state: FSMContext):
    await state.set_state(AddProductFSM.name)
    await message.answer("Введите название товара.")


@router.message(AddProductFSM.name)
async def get_product_name_to_add(message: types.Message, state: FSMContext):
    product_name = message.text.strip()

    async with SessionLocal() as session:
        product_service = ProductService(session)
        product = await product_service.create_product(product_name)

        if product is None:
            await message.answer(f"Товар {product_name} уже есть в базе")
            await send_product_menu(message, state)
            return

        generated_synonyms = await ai_service_mini.generate_synonyms(product_name) or []
        added_synonyms = await product_service.add_synonyms(product, generated_synonyms)

    await state.update_data(product_name=product_name)
    await state.set_state(AddProductFSM.manual_synonyms)

    if added_synonyms:
        synonyms_text = "\n".join(f"- {synonym.synonym}" for synonym in added_synonyms)
        text = (
            f"Товар {product_name} зарегистрирован в базе.\n"
            f"ИИ предложил и добавил синонимы:\n{synonyms_text}\n\n"
            "Можете отправить дополнительный синоним сообщением или нажать кнопку 'Пропустить'."
        )
    else:
        text = (
            f"Товар {product_name} зарегистрирован в базе.\n"
            "ИИ не предложил новых синонимов.\n\n"
            "Можете отправить дополнительный синоним сообщением или нажать кнопку 'Пропустить'."
        )

    await message.answer(text, reply_markup=skip_synonym_kb)


@router.message(AddProductFSM.manual_synonyms)
async def get_manual_product_synonyms(message: types.Message, state: FSMContext):
    if message.text.strip() == SKIP_SYNONYM_TEXT:
        await send_product_menu(message, state)
        return

    data = await state.get_data()
    product_name = data["product_name"]
    synonym = message.text.strip()

    async with SessionLocal() as session:
        product_service = ProductService(session)
        product = await product_service.get_product_by_name(product_name)

        if product is None:
            await message.answer(f"Товар {product_name} не найден в базе")
            await send_product_menu(message, state)
            return

        added_synonyms = await product_service.add_synonyms(product, [synonym])

    if added_synonyms:
        text = (
            f"Для товара {product_name} добавлен синоним: {added_synonyms[0].synonym}\n"
            "Можете отправить еще один дополнительный синоним или нажать 'Пропустить'."
        )
    else:
        text = (
            f"Синоним '{synonym}' не был добавлен для товара {product_name}\n"
            "Возможно, он уже существует. Можете отправить другой синоним или нажать 'Пропустить'."
        )

    await message.answer(text, reply_markup=skip_synonym_kb)


@router.message("/список", ProductFSM.command)
async def get_products(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        product_service = ProductService(session)
        products = await product_service.get_all_product_names()

    if products:
        text = "Список товаров:\n" + "\n".join(products)
    else:
        text = "Список товаров пуст"

    await message.answer(text)
    await send_product_menu(message, state)
