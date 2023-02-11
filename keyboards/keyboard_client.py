from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

b1 = KeyboardButton('Помощь 🔎')
b2 = KeyboardButton('Рефералы 👥')
b3 = KeyboardButton('Тарифы 👛')
b4 = KeyboardButton('Выбрать категорию 📋')
b5 = KeyboardButton('Привязать аккаунт 📎')

cl_kb = ReplyKeyboardMarkup(resize_keyboard = True)
cl_kb.row(b1, b2).row(b3, b5).add(b4)
