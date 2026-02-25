from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


admin_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='/worker')]],
    resize_keyboard=True)


user_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='/report')]],
    resize_keyboard=True
)


def get_kb(is_admin: bool) -> ReplyKeyboardMarkup:
    if is_admin:
        return admin_kb
    else:
        return user_kb