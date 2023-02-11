import datetime
from threading import Thread
import asyncio

from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types.message import ContentType

from create_bot_wb import bot, dp
from keyboards import keyboard_client as kb
from inline_keyboards import menu
import config as cfg
from database.sqlite_db import Use
from bot_buyer import bot_wb
from other import other
from inline_keyboards import client_in as in_cl

db = Use()


async def start(message: types.Message):
    txt = await db.get_msg(str(message.text.split(' ')[0]))
    try:
        await message.answer(txt, parse_mode='HTML', reply_markup=kb.cl_kb)
    except:
        pass

    await db.add_user(message.from_user.id, message.from_user.username, datetime.datetime.today().strftime('%d/%m/%y'))
    await db.add_status_user(message.from_user.id, 'inactive')
    await db.set_link_status(message.from_user.id, 'inactive')
    await db.set_profile_status(message.from_user.id, 'inactive')
    await db.add_count_send(message.from_user.id, 0)
    await db.add_sub_day(str(message.from_user.id))

    if len(message.text) > 6:
        if str(message.text.split(' ')[1]) != str(message.from_user.id):
            if await db.exist_user(message.text.split(' ')[1]):
                if not await db.exist_referral(message.from_user.id):
                    await db.add_referral(message.text.split(' ')[1], message.from_user.id)

                    referral_name = message.from_user.username
                    referrer_name = await db.get_fullname(message.text.split(' ')[1])

                    await message.answer(f'Вы стали рефералом {referrer_name}')
                    try:
                        await bot.send_message(message.text.split(' ')[1], f'{referral_name} стал вашим рефералом')
                    except:
                       pass
                    
                    # Прибавление дня
                    referrer_id = message.text.split(' ')[1]
                    status = await db.get_status_user(str(referrer_id))
                    if status[0] == 'active':
                        cur_days = await db.get_sub_days(referrer_id)
                        new_days = int(cur_days)-1
                        await db.update_sub_days(referrer_id, int(new_days))


async def help(message: types.Message):
    txt = await db.get_msg(str(message.text))
    try:
        await message.answer(txt, parse_mode='HTML', reply_markup=kb.cl_kb)
    except:
        pass


async def rate(message: types.Message):
    status = await db.get_status_user(message.from_user.id)
    f'У вас уже есть подписка\n' \
    f'<b>Подписка истечёт через:</b> 0 дней'
    if status[0] == 'active':
        days = await db.get_sub_days(message.from_user.id)
        if days < 0:
            new_days = days - int(cfg.sub_days)
            if new_days < 0:
                txt = f'У вас уже есть подписка\n' \
                      f'<b>Подписка истечёт через:</b> {int(new_days) * -1} дней'
            else:
                txt = f'У вас уже есть подписка\n' \
                      f'<b>Подписка истечёт через:</b> {int(new_days)} дней'
        else:
            new_days = int(cfg.sub_days) - days
            if new_days < 0:
                txt = f'У вас уже есть подписка\n' \
                      f'<b>Подписка истечёт через:</b> {int(new_days) * -1} дней'
            else:
                txt = f'У вас уже есть подписка\n' \
                      f'<b>Подписка истечёт через:</b> {int(new_days)} дней'
                
        try:
            await message.answer(txt, parse_mode='HTML')
        except:
            pass

    else:
        txt = str(await db.get_msg(str(message.text)))
        try:
            await message.answer(txt, parse_mode='HTML', reply_markup=in_cl.buy_but)
        except:
            pass


async def referral(message: types.Message):
    txt = await db.get_msg(str(message.text))
    try:
        await message.answer(txt.replace('<ссылка>', f'https://t.me/Premium_WB_SalesBot?start={message.from_user.id}').replace('<кол-во>', str(await db.get_count_referrals(message.from_user.id))),
                             parse_mode='HTML', reply_markup=kb.cl_kb)
    except:
        pass


async def choosing_a_category(message: types.Message):
    global mes_del
    await message.delete()
    mes_del = await message.answer('Выбор категории 📋', reply_markup=await menu.good_cat(cfg.categories, message.from_user.id))


# Покупка
@dp.callback_query_handler(lambda call: call.data == 'buy_sub')
async def buy_sub(callback_query: types.CallbackQuery):
    user_status = await db.get_status_user(callback_query.from_user.id)

    # pay data
    pay_data = await db.get_pay_inf()
    if not pay_data:
        await bot.send_message(callback_query.from_user.id, 'Администратор не указал информацию о плажете\n'
                                                            'Обратитесь к нему')
    else:

        PRICE = types.LabeledPrice(label=pay_data[2], amount=pay_data[2] * 100)
        if user_status[0] == 'inactive':
            await bot.send_invoice(callback_query.from_user.id,
                                   title=pay_data[3],
                                   description=pay_data[4],
                                   provider_token=cfg.PAYMENTS_TOKEN,
                                   currency='rub',
                                   photo_size=600,
                                   photo_width=300,
                                   photo_height=300,
                                   photo_url=pay_data[1],
                                   is_flexible=False,
                                   prices=[PRICE],
                                   start_parameter='one-month-subscription',
                                   payload='buy-prod')
        else:
            text = '<b>Ошибка</b>\n' \
                   'У вас уже есть подписка'
            await bot.send_message(callback_query.from_user.id, text, parse_mode='HTML')

        await bot.answer_callback_query(callback_query.id)


@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query_handler(check: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(check.id, ok=True)


# Успешный платёж
async def successful_payment(message: types.Message):
    await db.update_user_status(str(message.from_user.id), 'active')
    await db.update_sub_days(str(message.from_user.id), 0)
    text = '<b>Успешно ✅</b>\n' \
           'У вас появились новые возможности:\n' \
           '    ● Покупать товары не заходя на сайт\n' \
           '    ● Неограниченное количество товаров\n' \
           '' \
           'ВАЖНО! Чтобы иметь возможность покупать, необходимо привязать аккаунт'

    await message.answer(text, parse_mode='HTML', reply_markup=kb.cl_kb)


# Взаимодействие с меню
@dp.callback_query_handler(lambda call: True)
async def menu_cat(callback_query: types.CallbackQuery):
    # Убрать меню
    if callback_query.data == 'del':
        try:
            await bot.delete_message(callback_query.from_user.id, mes_del.message_id)
        except:
            pass

    # Проставление галочек
    elif callback_query.data in cfg.categories:
        # Если user уже выбирал категории
        if await db.get_user_categories(callback_query.from_user.id):
            user_categories = [i[0] for i in await db.get_user_categories(callback_query.from_user.id)]

            # Если данная категория не была выбрана - поставить галочку
            if callback_query.data not in user_categories:
                await db.add_user_category(callback_query.from_user.id, callback_query.data)
                await callback_query.message.edit_reply_markup(await menu.good_cat(cfg.categories, callback_query.from_user.id))

            # Убрать галочку
            else:
                await db.delete_user_category(callback_query.from_user.id, callback_query.data)
                await callback_query.message.edit_reply_markup(await menu.good_cat(cfg.categories, callback_query.from_user.id))

        # Если не выбирал
        else:
            await db.add_user_category(callback_query.from_user.id, callback_query.data)
            await callback_query.message.edit_reply_markup(await menu.good_cat(cfg.categories, callback_query.from_user.id))


    # Просто кнопка купить
    elif 'buy' in callback_query.data and 'size' not in callback_query.data:
        prod_id = callback_query.data.split('_')[1]
        link = await db.get_good_link(str(prod_id))
        loop = asyncio.get_event_loop()

        # Разрешение на запуск
        if await db.exist_count_browser():
            print('Есть очередь. Ожидаю')
            for _ in range(1000):
                if await db.get_count_browsers() < cfg.count_browser:
                    buy = Thread(target=bot_wb.buy_prod, args=(callback_query.from_user.id, False, link[0], loop))
                    buy.start()
                    print('Дождался. Запускаю')
                    break
                else:
                    await asyncio.sleep(0.5)
        else:
            print('Очереди нет. Запускаю')
            buy = Thread(target=bot_wb.buy_prod, args=(callback_query.from_user.id, False, link[0], loop))
            buy.start()


    # Кнопка с размерами
    elif 'buy' in callback_query.data and 'size' in callback_query.data:
        prod_id = str(callback_query.data.split('_')[2])
        await callback_query.message.edit_reply_markup(await menu.choice_size(prod_id))


    # Покупка с размерами
    elif 'size' in callback_query.data and 'buy' not in callback_query.data:
        size = str(callback_query.data.split('_')[1])
        prod_id = str(callback_query.data.split('_')[2])
        link = await db.get_good_link(str(callback_query.data.split('_')[2]))
        loop = asyncio.get_event_loop()

        await callback_query.message.edit_reply_markup(await menu.button_size_buy(prod_id))

        # Разрешение на запуск
        if await db.exist_count_browser():
            print('Есть очередь. Ожидаю')
            for _ in range(1000):
                if await db.get_count_browsers() < cfg.count_browser:
                    buy = Thread(target=bot_wb.buy_prod, args=(callback_query.from_user.id, size, link[0], loop))
                    buy.start()
                    print('Дождался. Запускаю')
                    break
                else:
                    await asyncio.sleep(0.5)
        else:
            print('Очереди нет. Запускаю')
            buy = Thread(target=bot_wb.buy_prod, args=(callback_query.from_user.id, size, link[0], loop))
            buy.start()





class FSM_link_account(StatesGroup):
    number = State()

async def link_an_account(message: types.Message):
    # Проверка статуса пользователя
    user_status = await db.get_status_user(message.from_user.id)
    if user_status[0] == 'active':

        # Проверка наличия профиля
        status_profile = await db.select_profile_status(message.from_user.id)
        if status_profile[0] == 'inactive':

            # Проверка текущего статуса привязки
            code = await db.select_link_status(message.from_user.id)
            if code[0] == 'inactive':
                await message.answer('<b>Привязка кнопки</b>\n'
                                     'Пришлите ваш номер (10 цифр)\n'
                                     '<b>Пример: </b><i>9612158000</i>', reply_markup=kb.cl_kb, parse_mode='HTML')
                await FSM_link_account.number.set()

            else:
                await message.answer('<b>Ошибка</b>\n'
                                     'В данный момент у вас запущен процесс привязки', parse_mode='HTML', reply_markup=kb.cl_kb)
        else:
            await message.answer('<b>Ошибка</b>\n'
                                 'Ваш аккаунт уже привязан', parse_mode='HTML', reply_markup=kb.cl_kb)
    else:
        await message.answer('<b>Ошибка</b>\n'
                             'Вы ещё не приобрели доступ', parse_mode='HTML', reply_markup=kb.cl_kb)

async def link_an_account_1(message: types.Message, state: FSMContext):
    db = Use()
    # Проверка номера
    if await other.check_number(message.text):
        # Разрешение на запуск
        if await db.exist_count_browser():
            await message.answer('Ожидайте...')
            for _ in range(1000):
                if await db.get_count_browsers() < cfg.count_browser:
                    await message.answer('Пришлите код, который поступит вам на телефон в ближайшие 2 минуты\n'
                                         'Через `/send_code` код', parse_mode='MARKDOWN', reply_markup=kb.cl_kb)

                    loop = asyncio.get_event_loop()
                    test = Thread(target=bot_wb.save_user_profile, args=(str(message.text), message.from_user.id, loop))
                    test.start()
                    break
                else:
                    await asyncio.sleep(0.5)
        else:
            await message.answer('Пришлите код, который поступит вам на телефон в ближайшие 2 минуты\n'
                                 'Через `/send_code` код', parse_mode='MARKDOWN', reply_markup=kb.cl_kb)

            loop = asyncio.get_event_loop()
            test = Thread(target=bot_wb.save_user_profile, args=(str(message.text), message.from_user.id, loop))
            test.start()

    else:
        await message.answer('<b>Неверно введён номер</b>\n'
                             'Исключите "+7" и "8" в начале номера\n'
                             '<b>Пример:</b> <i>9612158000 (10 цифр)</i>', parse_mode='HTML', reply_markup=kb.cl_kb)
    await state.finish()



async def get_code(message: types.Message):
    status = await db.select_link_status(message.from_user.id)
    if status[0] == 'active':
        code = await db.async_get_user_code(message.from_user.id)
        if not code:
            if len(message.text) > len('/send_code '):
                code = message.text.split(' ')[1]
                await db.async_add_user_code(message.from_user.id, code)
                await message.answer('Мы приняли ваш код, ожидайте', reply_markup=kb.cl_kb)
            else:
                await message.answer('Вы не ввели код\n'
                                     '`/send_code` код', parse_mode='MARKDOWN', reply_markup=kb.cl_kb)
        else:
            await db.async_update_user_code(message.from_user.id, str(message.text.split(' ')[1]))
            await message.answer('Мы приняли ваш код, ожидайте', reply_markup=kb.cl_kb)
    else:
        await message.answer('<b>Ошибка</b>\n'
                             'Вы не ожидаете кода', reply_markup=kb.cl_kb, parse_mode='HTML')


async def captcha(message: types.Message):
    status = await db.select_link_status(message.from_user.id)
    if status[0] == 'active':
        captcha = await db.async_get_user_captcha(message.from_user.id)
        if not captcha:
            if len(message.text) > len('/captcha '):
                await db.async_add_user_captcha(message.from_user.id, message.text.split(' ')[1])
                await message.answer('Расшифровка получена, ожидайте', reply_markup=kb.cl_kb)
            else:
                await message.answer('Ошибка\n'
                                     'Вы не ввели расшифровку\n'
                                     '`/send_captcha` код', reply_markup=kb.cl_kb, parse_mode='MARKDOWN')
        else:
            await message.answer('<b>Ошибка</b>\n'
                                 'Вы уже ввели расшифровку', reply_markup=kb.cl_kb, parse_mode='HTML')
    else:
        await message.answer('<b>Ошибка</b>\n'
                             'В данный момент вам не нужно ничего расшифровывать', parse_mode='HTML')



async def get_id(message: types.Message):
    await message.answer(f'Ваш ID: {message.from_user.id}', reply_markup=kb.cl_kb)







def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(start, commands=['start'], chat_type='private')
    dp.register_message_handler(help, Text(equals='Помощь 🔎'), chat_type='private')
    dp.register_message_handler(rate, Text(equals='Тарифы 👛'), chat_type='private')
    dp.register_message_handler(referral, Text(equals='Рефералы 👥'), chat_type='private')
    dp.register_message_handler(choosing_a_category, Text(equals='Выбрать категорию 📋'), chat_type='private')

    dp.register_message_handler(link_an_account, Text(equals='Привязать аккаунт 📎'), chat_type='private')
    dp.register_message_handler(link_an_account_1, state=FSM_link_account.number, chat_type='private')

    dp.register_message_handler(get_code, commands=['send_code'], chat_type='private')
    dp.register_message_handler(captcha, commands=['captcha'], chat_type='private')

    dp.register_message_handler(successful_payment, content_types=ContentType.SUCCESSFUL_PAYMENT, chat_type='private')
    dp.register_message_handler(get_id, commands=['id'], chat_type='private')
