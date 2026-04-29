from decimal import Decimal, InvalidOperation

from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.session import SessionLocal
from handlers.start import send_start_menu
from keyboards import rates_chapter_kb
from repositories.operation_repository import OperationRepository
from services.operation_type_service import OperationTypeService
from services.product_service import ProductService
from services.rate_service import RateService

router = Router()


class RatesFSM(StatesGroup):
    command = State()


class AddRateFSM(StatesGroup):
    operation_name = State()
    product_name = State()
    rate_value = State()


class UpdateRateFSM(StatesGroup):
    operation_name = State()
    product_name = State()
    rate_value = State()


class DeactivateRateFSM(StatesGroup):
    operation_name = State()
    product_name = State()


async def send_rates_menu(message: types.Message, state: FSMContext):
    firstname = message.from_user.first_name or ""
    text = f"""
Привет, <b>администратор {firstname}</b>.
<i>Основные команды этого раздела:</i>
- /list - список тарифов
- /add - добавить тариф
- /update - изменить тариф
- /deactivate - деактивировать тариф
"""
    await state.set_state(RatesFSM.command)
    await message.answer(text, reply_markup=rates_chapter_kb, parse_mode=ParseMode.HTML)


async def send_operation_names(message: types.Message, session) -> bool:
    operation_service = OperationTypeService(session)
    operations = await operation_service.get_all_operation_types()
    if not operations:
        await message.answer("Список операций пуст.")
        return False

    await message.answer("Доступные операции:\n" + "\n".join(operation.name for operation in operations))
    return True


async def send_product_names(message: types.Message, session) -> bool:
    product_service = ProductService(session)
    products = await product_service.get_all_product_names()
    if not products:
        await message.answer("Список товаров пуст.")
        return False

    await message.answer("Доступные товары:\n" + "\n".join(products))
    return True


def parse_rate_value(raw_value: str) -> Decimal | None:
    try:
        value = Decimal(raw_value.replace(",", ".").strip())
    except (InvalidOperation, AttributeError):
        return None
    if value <= 0:
        return None
    return value


@router.message(F.text.lower() == "/rates")
async def rates_chapter(message: types.Message, state: FSMContext, is_admin: bool):
    if not is_admin:
        return
    await send_rates_menu(message, state)


@router.message(F.text.lower() == "/back", RatesFSM.command)
@router.message(F.text.lower() == "/back", AddRateFSM.operation_name)
@router.message(F.text.lower() == "/back", AddRateFSM.product_name)
@router.message(F.text.lower() == "/back", AddRateFSM.rate_value)
@router.message(F.text.lower() == "/back", UpdateRateFSM.operation_name)
@router.message(F.text.lower() == "/back", UpdateRateFSM.product_name)
@router.message(F.text.lower() == "/back", UpdateRateFSM.rate_value)
@router.message(F.text.lower() == "/back", DeactivateRateFSM.operation_name)
@router.message(F.text.lower() == "/back", DeactivateRateFSM.product_name)
async def back_to_start(message: types.Message, state: FSMContext, is_admin: bool):
    await state.clear()
    await send_start_menu(message, state, is_admin)


@router.message(F.text.lower() == "/add", RatesFSM.command)
async def add_rate(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        has_operations = await send_operation_names(message, session)
    if not has_operations:
        await send_rates_menu(message, state)
        return

    await state.set_state(AddRateFSM.operation_name)
    await message.answer("Введите название операции для нового тарифа.")


@router.message(AddRateFSM.operation_name)
async def add_rate_get_operation(message: types.Message, state: FSMContext):
    operation_name = (message.text or "").strip()

    async with SessionLocal() as session:
        operation_service = OperationTypeService(session)
        operation = await operation_service.get_operation_type_by_name(operation_name)
        if operation is None:
            await message.answer("Операция не найдена. Введите название из списка.")
            return

        await state.update_data(operation_name=operation.name)
        has_products = await send_product_names(message, session)

    if not has_products:
        await send_rates_menu(message, state)
        return

    await state.set_state(AddRateFSM.product_name)
    await message.answer("Введите название товара для нового тарифа.")


@router.message(AddRateFSM.product_name)
async def add_rate_get_product(message: types.Message, state: FSMContext):
    product_name = (message.text or "").strip()

    async with SessionLocal() as session:
        product_service = ProductService(session)
        product = await product_service.get_product_by_name(product_name)
        if product is None:
            await message.answer("Товар не найден. Введите название из списка.")
            return

    await state.update_data(product_name=product_name)
    await state.set_state(AddRateFSM.rate_value)
    await message.answer("Введите значение тарифа.")


@router.message(AddRateFSM.rate_value)
async def add_rate_get_value(message: types.Message, state: FSMContext):
    rate_value = parse_rate_value(message.text or "")
    if rate_value is None:
        await message.answer("Введите корректное положительное число.")
        return

    data = await state.get_data()
    operation_name = data["operation_name"]
    product_name = data["product_name"]

    async with SessionLocal() as session:
        operation_service = OperationTypeService(session)
        product_service = ProductService(session)
        rate_service = RateService(session)

        operation = await operation_service.get_operation_type_by_name(operation_name)
        product = await product_service.get_product_by_name(product_name)
        if operation is None or product is None:
            await message.answer("Не удалось найти операцию или товар.")
            await send_rates_menu(message, state)
            return

        rate = await rate_service.create_rate(operation.id, product.id, int(rate_value))

    if rate is None:
        await message.answer("Активный тариф для этой пары операция/товар уже существует.")
    else:
        await message.answer(
            f"Тариф добавлен: операция '{operation_name}', товар '{product_name}', значение {rate_value}."
        )

    await send_rates_menu(message, state)


@router.message(F.text.lower() == "/update", RatesFSM.command)
async def update_rate(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        has_operations = await send_operation_names(message, session)
    if not has_operations:
        await send_rates_menu(message, state)
        return

    await state.set_state(UpdateRateFSM.operation_name)
    await message.answer("Введите название операции для изменения тарифа.")


@router.message(UpdateRateFSM.operation_name)
async def update_rate_get_operation(message: types.Message, state: FSMContext):
    operation_name = (message.text or "").strip()

    async with SessionLocal() as session:
        operation_service = OperationTypeService(session)
        operation = await operation_service.get_operation_type_by_name(operation_name)
        if operation is None:
            await message.answer("Операция не найдена. Введите название из списка.")
            return

        await state.update_data(operation_name=operation.name)
        has_products = await send_product_names(message, session)

    if not has_products:
        await send_rates_menu(message, state)
        return

    await state.set_state(UpdateRateFSM.product_name)
    await message.answer("Введите название товара для изменения тарифа.")


@router.message(UpdateRateFSM.product_name)
async def update_rate_get_product(message: types.Message, state: FSMContext):
    product_name = (message.text or "").strip()

    async with SessionLocal() as session:
        product_service = ProductService(session)
        product = await product_service.get_product_by_name(product_name)
        if product is None:
            await message.answer("Товар не найден. Введите название из списка.")
            return

    await state.update_data(product_name=product_name)
    await state.set_state(UpdateRateFSM.rate_value)
    await message.answer("Введите новое значение тарифа.")


@router.message(UpdateRateFSM.rate_value)
async def update_rate_get_value(message: types.Message, state: FSMContext):
    rate_value = parse_rate_value(message.text or "")
    if rate_value is None:
        await message.answer("Введите корректное положительное число.")
        return

    data = await state.get_data()
    operation_name = data["operation_name"]
    product_name = data["product_name"]

    async with SessionLocal() as session:
        rate_service = RateService(session)
        rate = await rate_service.update_rate(product_name, operation_name, rate_value)

    if rate is None:
        await message.answer("Активный тариф для этой пары операция/товар не найден.")
    else:
        await message.answer(
            f"Тариф обновлён: операция '{operation_name}', товар '{product_name}', новое значение {rate_value}."
        )

    await send_rates_menu(message, state)


@router.message(F.text.lower() == "/deactivate", RatesFSM.command)
async def deactivate_rate(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        has_operations = await send_operation_names(message, session)
    if not has_operations:
        await send_rates_menu(message, state)
        return

    await state.set_state(DeactivateRateFSM.operation_name)
    await message.answer("Введите название операции для деактивации тарифа.")


@router.message(DeactivateRateFSM.operation_name)
async def deactivate_rate_get_operation(message: types.Message, state: FSMContext):
    operation_name = (message.text or "").strip()

    async with SessionLocal() as session:
        operation_service = OperationTypeService(session)
        operation = await operation_service.get_operation_type_by_name(operation_name)
        if operation is None:
            await message.answer("Операция не найдена. Введите название из списка.")
            return

        await state.update_data(operation_name=operation.name)
        has_products = await send_product_names(message, session)

    if not has_products:
        await send_rates_menu(message, state)
        return

    await state.set_state(DeactivateRateFSM.product_name)
    await message.answer("Введите название товара для деактивации тарифа.")


@router.message(DeactivateRateFSM.product_name)
async def deactivate_rate_get_product(message: types.Message, state: FSMContext):
    product_name = (message.text or "").strip()
    data = await state.get_data()
    operation_name = data["operation_name"]

    async with SessionLocal() as session:
        product_service = ProductService(session)
        product = await product_service.get_product_by_name(product_name)
        if product is None:
            await message.answer("Товар не найден. Введите название из списка.")
            return

        rate_service = RateService(session)
        rate = await rate_service.deactivate_rate(product_name, operation_name)

    if rate is None:
        await message.answer("Активный тариф для этой пары операция/товар не найден.")
    else:
        await message.answer(
            f"Тариф деактивирован: операция '{operation_name}', товар '{product_name}'."
        )

    await send_rates_menu(message, state)


@router.message(F.text.lower() == "/list", RatesFSM.command)
async def get_rates(message: types.Message, state: FSMContext):
    async with SessionLocal() as session:
        rate_service = RateService(session)
        operation_repository = OperationRepository(session)
        rates = await rate_service.get_rates()

        if not rates:
            await message.answer("Список тарифов пуст.")
            await send_rates_menu(message, state)
            return

        lines: list[str] = []
        for rate in rates:
            operation = await operation_repository.get_operation_type_by_id(rate.operation_id)
            product = await operation_repository.get_product_by_id(rate.product_id)
            operation_name = operation.name if operation else f"id={rate.operation_id}"
            product_name = product.name if product else f"id={rate.product_id}"
            status = "активен" if rate.is_active else "неактивен"
            lines.append(
                f"{operation_name} | {product_name} | {rate.rate} | {status} | c {rate.valid_from}"
            )

    await message.answer("Список тарифов:\n" + "\n".join(lines))
    await send_rates_menu(message, state)
