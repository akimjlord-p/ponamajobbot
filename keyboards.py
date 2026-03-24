from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


main_admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/воркер"),
            KeyboardButton(text="/аналитика"),
            KeyboardButton(text="/товары"),
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
    ]
)

worker_chapter_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/список"),
            KeyboardButton(text="/добавить"),
            KeyboardButton(text="/удалить"),
        ]
    ]
)

product_chapter_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/список"),
            KeyboardButton(text="/добавить"),
        ]
    ]
)


def get_main_kb(is_admin: bool) -> ReplyKeyboardMarkup:
    if is_admin:
        return main_admin_kb
    return main_worker_kb
