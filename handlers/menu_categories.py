from aiogram import Dispatcher, types
from aiogram.types import ContentType
from aiogram.dispatcher.filters import Text

from create_bot_wb import bot, dp
from keyboards import keyboard_client as kb
from inline_keyboards import menu


#
#
# @dp.callback_query_handler(lambda call: True)
# async def test(callback_query: types.CallbackQuery):
#     print('ХУЙ')
#     # main_cat = callback_query.data
#     # print(main_cat)
#     # print('asdasd')

