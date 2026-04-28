from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


main_admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/воркер"),
            KeyboardButton(text="/ии"),
            KeyboardButton(text="/товары")
        ],
        [
            KeyboardButton(text="/операции"),
            KeyboardButton(text="/тарифы"),
        ]
    ],
    resize_keyboard=True,
)

main_worker_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/чекин"),
            KeyboardButton(text="/чекаут"),
            KeyboardButton(text="/комент"),
        ]
    ],
    resize_keyboard=True,
)

worker_chapter_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/список"),
            KeyboardButton(text="/добавить")
        ],
        [
            KeyboardButton(text="/удалить"),
            KeyboardButton(text="/назад"),
        ]
    ],
    resize_keyboard=True,
)

product_chapter_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/список"),
            KeyboardButton(text="/добавить"),
            KeyboardButton(text="/назад"),
        ]
    ],
    resize_keyboard=True,
)

operation_chapter_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/список"),
            KeyboardButton(text="/добавить"),
            KeyboardButton(text="/назад"),
        ]
    ],
    resize_keyboard=True,
)

ai_chapter_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/вопрос"),
            KeyboardButton(text="/контекст"),
            KeyboardButton(text="/назад"),
        ]
    ],
    resize_keyboard=True,
)

rates_chapter_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/список"),
            KeyboardButton(text="/добавить"),
            KeyboardButton(text="/изменить")
        ],
        [
            KeyboardButton(text="/деактивировать"),
            KeyboardButton(text="/назад"),
        ]
    ],
    resize_keyboard=True,
)


def get_main_kb(is_admin: bool) -> ReplyKeyboardMarkup:
    if is_admin:
        return main_admin_kb
    return main_worker_kb
