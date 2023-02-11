from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


buy_but = InlineKeyboardMarkup()
but = InlineKeyboardButton(text='Купить подписку 👛', callback_data='buy_sub')
buy_but.add(but)