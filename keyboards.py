from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


admin_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='/worker')]],
    resize_keyboard=True)


user_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='/report')]],
    resize_keyboard=True
)