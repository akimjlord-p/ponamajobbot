from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


main_admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/workers"),
            KeyboardButton(text="/ai"),
            KeyboardButton(text="/products"),
        ],
        [
            KeyboardButton(text="/operations"),
            KeyboardButton(text="/rates"),
        ],
        [
            KeyboardButton(text="/checkin"),
            KeyboardButton(text="/checkout"),
            KeyboardButton(text="/comment"),
        ],
    ],
    resize_keyboard=True,
)

main_worker_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/checkin"),
            KeyboardButton(text="/checkout"),
            KeyboardButton(text="/comment"),
        ]
    ],
    resize_keyboard=True,
)

worker_chapter_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/list"),
            KeyboardButton(text="/add")
        ],
        [
            KeyboardButton(text="/delete"),
            KeyboardButton(text="/back"),
        ]
    ],
    resize_keyboard=True,
)

product_chapter_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/list"),
            KeyboardButton(text="/add"),
            KeyboardButton(text="/back"),
        ]
    ],
    resize_keyboard=True,
)

operation_chapter_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/list"),
            KeyboardButton(text="/add"),
            KeyboardButton(text="/back"),
        ]
    ],
    resize_keyboard=True,
)

ai_chapter_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/question"),
            KeyboardButton(text="/context"),
            KeyboardButton(text="/show_context"),
        ],
        [
            KeyboardButton(text="/back"),
        ]
    ],
    resize_keyboard=True,
)

rates_chapter_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/list"),
            KeyboardButton(text="/add"),
            KeyboardButton(text="/update")
        ],
        [
            KeyboardButton(text="/deactivate"),
            KeyboardButton(text="/back"),
        ]
    ],
    resize_keyboard=True,
)


def get_main_kb(is_admin: bool) -> ReplyKeyboardMarkup:
    if is_admin:
        return main_admin_kb
    return main_worker_kb
