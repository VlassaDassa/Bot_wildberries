from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.sqlite_db import Use

db = Use()

# Клавиатура
async def good_cat(data, user_id):
    cat = InlineKeyboardMarkup()
    but_list = []

    for name in data:
        if await db.get_user_categories(user_id):
            user_categories = [i[0] for i in await db.get_user_categories(user_id)]
            if name in user_categories:
                but_list.append(InlineKeyboardButton(text=f'✅ {name}', callback_data=name))
            else:
                but_list.append(InlineKeyboardButton(text=name, callback_data=name))
        else:
            but_list.append(InlineKeyboardButton(text=name, callback_data=name))

    cat.add(*but_list)
    cat.row(InlineKeyboardButton(text='Убрать меню ❌', callback_data=f'del'))

    return cat

async def link_to_prod(link):
    link_btn = InlineKeyboardMarkup()
    link_btn.add(InlineKeyboardButton('Посмотреть', url=link))
    return link_btn


# Просто кнопка купить
async def button_buy(prod_id):
    buy = InlineKeyboardMarkup()

    link = await db.get_good_link(prod_id)

    buy.add(InlineKeyboardButton(text='Купить 👛', callback_data=f'buy_{prod_id}'))
    buy.add(InlineKeyboardButton(text='Посмотреть', url=link[0]))
    return buy


# Купить с выбором размера
async def button_size_buy(prod_id):
    buy = InlineKeyboardMarkup()

    link = await db.get_good_link(prod_id)

    buy.add(InlineKeyboardButton(text='Купить 👛', callback_data=f'size_buy_{prod_id}'))
    buy.add(InlineKeyboardButton(text='Посмотреть', url=link[0]))
    return buy


# Выбор размера
async def choice_size(prod_id):
    but_size = InlineKeyboardMarkup()
    sizes = await db.get_good_sizes(prod_id)
    but_list = []

    for size in sizes[0].split(', '):
        but_list.append(InlineKeyboardButton(text=size, callback_data=f'size_{size}_{prod_id}'))
    but_size.add(*but_list)
    return but_size





