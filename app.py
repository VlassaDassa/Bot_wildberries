from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from create_bot_wb import dp, bot
from handlers import client
from handlers import admin
from parser.parser import checker_and_sender, start_parsing
from database.sqlite_db import Use
import config as cfg
from keyboards import keyboard_client as cl_kb










db = Use()
async def on_startup(_):
    # await test()
    print('Bot online\n')

    # Парсинг
    pars_scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    pars_scheduler.start()
    pars_scheduler.add_job(start_parsing, "interval", minutes=2)


    # Отправка товаров пользователям
    checker_scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    checker_scheduler.start()
    checker_scheduler.add_job(checker_and_sender, "interval", seconds=3)


    # Обновление количества отправлений обычным пользователям
    zeroing = AsyncIOScheduler(timezone="Europe/Moscow")
    zeroing.add_job(zeroing_count_send, 'cron', hour=23, minute=59)
    zeroing.start()

    # # Обновление подписки подписчиков
    # update_sub = AsyncIOScheduler(timezone="Europe/Moscow")
    # update_sub.add_job(sub_days_update, 'cron', hour=23, minute=59)
    # update_sub.start()


# Обнуление отправлений для бесплатников
async def zeroing_count_send():
    user_ids = await db.get_id_count_send()
    for user_id in user_ids:
        await db.update_count_send(str(user_id[0]), 0)


# # Обновление подписки пользователей
# async def sub_days_update():
#     sub_ids = await db.get_sub_ids()
#     for id in sub_ids:
#         days = await db.get_sub_days(id[0])
#         if days == cfg.sub_days - 1:
#             txt = '<b>Приветствуем! ✋</b>\n' \
#                 'Завтра ваша подписка подойдёт к концу'
#             await bot.send_message(id[0], txt, reply_markup=cl_kb.cl_kb, parse_mode='HTML')
#
#
#         elif days > cfg.sub_days:
#             txt = '<b>Приветствуем! ✋</b>\n' \
#                   'Увы, ваша подписка подошла к концу\n' \
#                   'Теперь вам недоступны все возможности этого бота\n' \
#                   'Вы можете исправить это, снова купив её'
#             await bot.send_message(id[0], txt, reply_markup=cl_kb.cl_kb, parse_mode='HTML')
#             await db.update_user_status(id[0], 'inactive')
#
#         else:
#             await db.update_sub_days(id[0], days+1)




client.register_handlers_client(dp)
admin.register_handlers_client(dp)



def main():
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

if __name__ == '__main__':
    main()
    






