from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

b1 = KeyboardButton('Изменить сообщения ✏')
b2 = KeyboardButton('Количество пользователей 👥')
b3 = KeyboardButton('Отправить всем сообщение ✉')
b4 = KeyboardButton('Вернуться 💤')
b5 = KeyboardButton('Изменить платёж 👛')
b6 = KeyboardButton('Выдать подписку')
adm_kb = ReplyKeyboardMarkup(resize_keyboard = True)
adm_kb.row(b1, b2).row(b3, b5).row(b4, b6)

remove_kb = ReplyKeyboardRemove()

cancel = KeyboardButton('Отменить ❌')
send = KeyboardButton('Отправить ✅')
send_or_cancel = ReplyKeyboardMarkup(resize_keyboard=True)
send_or_cancel.row(cancel, send)


help = KeyboardButton('Помощь 🔎')
referral = KeyboardButton('Рефералы 👥')
rate = KeyboardButton('Тарифы 👛')
start_msg = KeyboardButton('Стартовое сообщение')
choice_edit_btn = ReplyKeyboardMarkup(resize_keyboard=True)
choice_edit_btn.row(help, referral).row(rate, start_msg)


save = KeyboardButton('Сохранить 💾')
cancel_or_edit = ReplyKeyboardMarkup(resize_keyboard=True)
cancel_or_edit.row(save, cancel)


cancel = KeyboardButton('Отменить ❌')
send = KeyboardButton('Сохранить ✅')
pay_edit = ReplyKeyboardMarkup(resize_keyboard=True)
pay_edit.row(cancel, send)


user = KeyboardButton('Другому пользователю')
me = KeyboardButton('Себе')
choice_whom = ReplyKeyboardMarkup(resize_keyboard=True)
choice_whom.row(user, me)


async def count_days():
    return ReplyKeyboardMarkup(resize_keyboard=True).row(*[KeyboardButton(str(i)) for i in range(1, 8)])
